import os
import json
import bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models.schemas import TokenData
from database.redis_client import redis_client

# Use this for Depends() to extract the token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# In-memory user store (MVP)
# Key: email, Value: {email, hashed_password}
users_db = {}

JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_here")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))


def _user_key(email: str) -> str:
    return f"user:{email.lower()}"


def save_user(email: str, hashed_password: str) -> None:
    normalized = email.lower()
    user_obj = {"email": normalized, "hashed_password": hashed_password}
    users_db[normalized] = user_obj
    try:
        redis_client.set(_user_key(normalized), json.dumps(user_obj))
    except Exception:
        # Keep local behavior even if Redis is unavailable.
        pass


def get_user(email: str):
    normalized = email.lower()
    user_obj = users_db.get(normalized)
    if user_obj:
        return user_obj

    try:
        data = redis_client.get(_user_key(normalized))
        if data:
            parsed = json.loads(data)
            users_db[normalized] = parsed
            return parsed
    except Exception:
        pass

    return None


def user_exists(email: str) -> bool:
    return get_user(email) is not None

def hash_password(password: str) -> str:
    """Hashes a plaintext password string using bcrypt and a generated salt."""
    # bcrypt requires bytes
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plaintext password matches the previously generated bcrypt hash."""
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_bytes)

def create_access_token(data: dict) -> str:
    """Encodes a payload dictionary into a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Decodes the Bearer JWT token from the Request headers, validates the signature,
    and returns the authenticated user's email if valid. Raises HTTP 401 otherwise.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    if not token_data.email or not user_exists(token_data.email):
        raise credentials_exception

    return token_data.email
