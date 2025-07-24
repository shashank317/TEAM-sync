"""
schemas.py – Pydantic models mapped to new ORM & enums
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime
from models import Status

# ---------- User ----------

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ---------- Project ----------

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    title: str
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ---------- Attachment ----------

class AttachmentOut(BaseModel):
    id: int
    filename: str
    filepath: str

    model_config = ConfigDict(from_attributes=True)


# ---------- Comment ----------

class CommentCreate(BaseModel):
    content: str


class CommentOut(BaseModel):
    id: int
    content: str
    timestamp: datetime
    user_name: str


# ---------- Task ----------

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[Status] = Status.PENDING
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Status] = None
    due_date: Optional[datetime] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: Status
    due_date: Optional[datetime]
    attachments: List[AttachmentOut] = []
    comments: List[CommentOut] = []

    model_config = ConfigDict(from_attributes=True)


# ---------- Password & profile ----------

class PasswordReset(BaseModel):
    email: EmailStr
    new_password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
