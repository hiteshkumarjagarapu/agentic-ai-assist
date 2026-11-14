import asyncio

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.jwt_handler import create_token
from auth.models import User
from auth.schemas import TokenResponse, UserCreate, UserLogin, UserOut
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_for(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_token(user.id, user.email),
        user=UserOut(id=user.id, email=user.email, name=user.name),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    hashed = await asyncio.to_thread(
        lambda: bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    )
    user = User(email=email, name=data.name, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_for(user)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    ok = user is not None and await asyncio.to_thread(
        bcrypt.checkpw, data.password.encode(), user.password_hash.encode()
    )
    if not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return _token_for(user)  # type: ignore[arg-type]
