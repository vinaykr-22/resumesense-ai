import os
import json
import time
import fnmatch
from typing import Dict, Any, Optional, Tuple, List, Union

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class _InMemoryRedis:
    """
    Tiny Redis-like fallback for local dev on machines without Redis.
    Implements only what this repo uses: get/set/setex/exists/scan.
    """

    def __init__(self):
        self._data: Dict[str, Tuple[str, Optional[float]]] = {}

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._data.items() if exp is not None and exp <= now]
        for k in expired:
            self._data.pop(k, None)

    def get(self, key: str) -> Optional[str]:
        self._purge_expired()
        v = self._data.get(key)
        if not v:
            return None
        value, exp = v
        if exp is not None and exp <= time.time():
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str) -> bool:
        self._data[key] = (value, None)
        return True

    def setex(self, key: str, seconds: int, value: str) -> bool:
        self._data[key] = (value, time.time() + int(seconds))
        return True

    def incr(self, key: str) -> int:
        current = self.get(key)
        try:
            current_int = int(current) if current is not None else 0
        except ValueError:
            current_int = 0
        next_val = current_int + 1
        _, existing_exp = self._data.get(key, (None, None))
        self._data[key] = (str(next_val), existing_exp)
        return next_val

    def expire(self, key: str, seconds: int) -> bool:
        value = self.get(key)
        if value is None:
            return False
        self._data[key] = (value, time.time() + int(seconds))
        return True

    def ttl(self, key: str) -> int:
        self._purge_expired()
        value = self._data.get(key)
        if not value:
            return -2
        _, exp = value
        if exp is None:
            return -1
        remaining = int(exp - time.time())
        return remaining if remaining > 0 else -2

    def exists(self, key: str) -> int:
        return 1 if self.get(key) is not None else 0

    def scan(self, cursor: Union[str, int], match: str = "*", count: int = 10) -> Tuple[int, List[str]]:
        # Cursor is ignored; we return everything in one page for MVP.
        self._purge_expired()
        keys = [k for k in self._data.keys() if fnmatch.fnmatch(k, match)]
        return 0, keys[:count]


def _create_redis_client():
    if redis is None:
        return _InMemoryRedis()
    try:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return _InMemoryRedis()


redis_client = _create_redis_client()

def store_status(job_id: str, status_obj: Dict[str, Any], expire_seconds: int = 3600):
    status_key = f"status:{job_id}"
    redis_client.setex(status_key, expire_seconds, json.dumps(status_obj))

def get_status(job_id: str) -> Optional[Dict[str, Any]]:
    status_key = f"status:{job_id}"
    data = redis_client.get(status_key)
    if data:
        return json.loads(data)
    return None
