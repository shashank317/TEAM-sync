"""
routers/tasks.py – operates only on existing tasks (no duplicates)
"""

import os
from uuid import uuid4
from typing import List

from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File
)
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models, schemas

router = APIRouter(tags=["Tasks"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _owner_guard(task_id: int, db: Session, user: models.User):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    project = db.query(models.Project).filter(
        models.Project.id == task.project_id,
        models.Project.owner_id == user.id
    ).first()
    if not project:
        raise HTTPException(403, "Not authorized")
    return task


@router.patch("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = _owner_guard(task_id, db, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = _owner_guard(task_id, db, current_user)
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}


@router.post("/tasks/{task_id}/upload", response_model=schemas.AttachmentOut)
def upload_file(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = _owner_guard(task_id, db, current_user)
    filename = f"{uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(file.file.read())
    attach = models.FileAttachment(
        filename=file.filename,
        filepath=filepath,
        task_id=task_id
    )
    db.add(attach)
    db.commit()
    db.refresh(attach)
    return attach


@router.get("/tasks/{task_id}/attachments",
            response_model=List[schemas.AttachmentOut])
def list_attachments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = _owner_guard(task_id, db, current_user)
    return task.attachments
