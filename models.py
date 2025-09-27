"""
models.py – SQLAlchemy ORM models with cascades & enums
"""

from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

# ---------- Enums ----------

class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    DONE = "done"


# ---------- User ----------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    projects = relationship("Project", back_populates="owner",
                            cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user",
                            cascade="all, delete-orphan")
    memberships = relationship("ProjectMember", back_populates="user",
                               cascade="all, delete-orphan")


# ---------- Project ----------

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), index=True)

    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project",
                         cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project",
                           cascade="all, delete-orphan")


# ---------- Membership ----------

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    role = Column(String, default="editor")  # admin / editor / viewer

    user = relationship("User", back_populates="memberships")
    project = relationship("Project", back_populates="members")


# ---------- Task ----------

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default=Status.PENDING.value)
    due_date = Column(DateTime, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])
    attachments = relationship("FileAttachment", back_populates="task",
                               cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="task",
                            cascade="all, delete-orphan")


# ---------- Attachment ----------

class FileAttachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"))

    task = relationship("Task", back_populates="attachments")


# ---------- Comment ----------

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"), index=True)

    user = relationship("User")
    task = relationship("Task", back_populates="comments")
