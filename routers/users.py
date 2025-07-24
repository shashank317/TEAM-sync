"""
routers/users.py – user profile endpoints only
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, utils
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
def me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.name
    }


@router.put("/me")
def update_profile(
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if payload.name:
        current_user.name = payload.name

    if payload.email:
        if db.query(models.User).filter(
            models.User.email == payload.email,
            models.User.id != current_user.id
        ).first():
            raise HTTPException(400, "Email already used")
        current_user.email = payload.email

    if payload.new_password:
        if not payload.current_password or \
           not utils.verify_password(
               payload.current_password, current_user.password
           ):
            raise HTTPException(403, "Current password incorrect")
        current_user.password = utils.hash_password(payload.new_password)

    db.commit()
    return {"message": "Profile updated"}
