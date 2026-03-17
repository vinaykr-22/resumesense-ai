from fastapi import APIRouter, HTTPException, status
from models.schemas import UserRegister, UserLogin, Token
from services.auth import (
    users_db,
    hash_password,
    verify_password,
    create_access_token
)

router = APIRouter()

@router.post("/register", response_model=Token)
def register(user: UserRegister):
    if user.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )
    
    # Store user in in-memory dict
    users_db[user.email] = {
        "email": user.email,
        "hashed_password": hash_password(user.password)
    }
    
    # Auto-login after register
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(user: UserLogin):
    user_dict = users_db.get(user.email)
    if not user_dict or not verify_password(user.password, user_dict["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
