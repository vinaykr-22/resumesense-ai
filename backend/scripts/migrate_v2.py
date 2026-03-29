"""
V2 Data Migration Script
========================
Scans existing Redis keys and backfills V2 fields with safe defaults.
Idempotent — safe to re-run multiple times.

Usage:
    cd backend
    python scripts/migrate_v2.py
"""

import os
import sys
import json

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.redis_client import redis_client


def migrate_resume_keys():
    """Add version and parsed_content to existing resume:{id} keys."""
    cursor = "0"
    migrated = 0
    scanned = 0

    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match="resume:res_*", count=100)
        for key in keys:
            key_str = key.decode("utf-8") if isinstance(key, bytes) else str(key)
            scanned += 1
            raw = redis_client.get(key_str)
            if not raw:
                continue

            data = json.loads(raw)
            changed = False

            if "version" not in data:
                data["version"] = 1  # Mark pre-V2 data as version 1
                changed = True

            if "parsed_content" not in data:
                text = data.get("text", "")
                data["parsed_content"] = {"raw_text": text}
                changed = True

            if changed:
                # Preserve the original TTL if possible; fall back to 7 days
                ttl = redis_client.ttl(key_str)
                expire = ttl if ttl > 0 else 7 * 24 * 3600
                redis_client.setex(key_str, expire, json.dumps(data))
                migrated += 1

        if cursor == 0 or cursor == b"0":
            break

    print(f"  Resume keys: scanned={scanned}, migrated={migrated}")
    return migrated


def migrate_result_keys():
    """Add analysis_data structure to existing result:{id} keys."""
    cursor = "0"
    migrated = 0
    scanned = 0

    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match="result:res_*", count=100)
        for key in keys:
            key_str = key.decode("utf-8") if isinstance(key, bytes) else str(key)
            scanned += 1
            raw = redis_client.get(key_str)
            if not raw:
                continue

            data = json.loads(raw)
            changed = False

            if "analysis_data" not in data:
                # Build analysis_data from existing fields where possible
                skills = data.get("skills", {})
                all_skills = skills.get("all_skills", []) if isinstance(skills, dict) else []

                data["analysis_data"] = {
                    "ats_score": 0.0,
                    "ats_breakdown": {
                        "keyword_score": 0.0,
                        "section_completeness": 0.0,
                        "bullet_strength": 0.0,
                        "formatting_score": 0.0,
                    },
                    "weak_bullets": [],
                    "rewritten_bullets": [],
                    "extracted_skills": all_skills,
                    "job_match_data": {},
                    "learning_path": {},
                }
                changed = True

            if changed:
                ttl = redis_client.ttl(key_str)
                expire = ttl if ttl > 0 else 3600
                redis_client.setex(key_str, expire, json.dumps(data))
                migrated += 1

        if cursor == 0 or cursor == b"0":
            break

    print(f"  Result keys: scanned={scanned}, migrated={migrated}")
    return migrated


def main():
    print("V2 Migration — backfilling new fields into existing Redis data")
    print("-" * 60)
    migrate_resume_keys()
    migrate_result_keys()
    print("-" * 60)
    print("Migration complete. No existing data was removed.")


if __name__ == "__main__":
    main()
