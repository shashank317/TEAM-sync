"""
auth.py – JWT authentication & user auth endpoints
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, Response
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel, EmailStr

from database import get_db
from models import User
from utils import hash_password, verify_password

# ----------------- JWT Config -----------------

SECRET_KEY = os.getenv("JWT_SECRET", "teamsyncsecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
RESET_TOKEN_EXPIRE_MINUTES = 15

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Allow dependency to NOT auto-raise when header is missing; we'll fallback to cookie
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _create_token(data: dict, expires_minutes: int) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict) -> str:
    return _create_token(data, ACCESS_TOKEN_EXPIRE_MINUTES)


# ----------------- Helpers -----------------

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    # Try Authorization header first, then HTTP-only cookie
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[int] = payload.get("user_id")
        if not user_id:
            raise cred_exc
    except JWTError:
        raise cred_exc
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise cred_exc
    return user


def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Same as get_current_user but returns None instead of raising 401.

    Useful for endpoints that want to optionally authenticate and handle
    unauthenticated cases with redirects or custom responses.
    """
    try:
        if not token:
            token = request.cookies.get("access_token")
        if not token:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[int] = payload.get("user_id")
        if not user_id:
            return None
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except JWTError:
        return None


# ----------------- Schemas -----------------

class SignupInput(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginInput(BaseModel):
    email: EmailStr
    password: str


# ----------------- Public Endpoints -----------------

@router.post("/signup")
def signup(data: SignupInput, response: Response, db: Session = Depends(get_db)):
    try:
        # Check existing user
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(400, "Email already registered")
        # Create
        new_user = User(
            name=data.name,
            email=data.email,
            password=hash_password(data.password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        token = create_access_token({"user_id": new_user.id})
        # Set cookie for browser-based auth (keeps JSON response for existing frontend)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite=os.getenv("COOKIE_SAMESITE", "lax"),
            secure=os.getenv("COOKIE_SECURE", "0") == "1"  # True if behind HTTPS
        )
        return {"access_token": token}
    except OperationalError:
        # Database unreachable or SSL / network failure
        raise HTTPException(status_code=503, detail="Database unavailable. Please try again shortly.")


@router.post("/login")
def login(data: LoginInput, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token({"user_id": user.id})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=os.getenv("COOKIE_SAMESITE", "lax"),
        secure=os.getenv("COOKIE_SECURE", "0") == "1"  # True if behind HTTPS
    )
    return {"access_token": token}


# ----------------- Logout -----------------

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


# ----------------- Password Reset -----------------

@router.post("/request-password-reset")
def request_reset(email: EmailStr = Body(..., embed=True),
                  db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "No user with that email")
    reset_token = _create_token({"user_id": user.id},
                                RESET_TOKEN_EXPIRE_MINUTES)
    link = f"http://localhost:8000/auth/reset-password?token={reset_token}"
    return {"reset_link": link}


@router.post("/reset-password")
def perform_reset(token: str = Body(...),
                  new_password: str = Body(...),
                  db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except JWTError:
        raise HTTPException(400, "Invalid or expired reset token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.password = hash_password(new_password)
    db.commit()
    return {"message": "Password updated"}