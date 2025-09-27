"""
routers/projects.py – owns projects & project-scoped tasks upload
"""

import os
import shutil
from datetime import datetime
from uuid import uuid4
from typing import List

from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form
)
from sqlalchemy.orm import Session, joinedload
from database import get_db
from auth import get_current_user
import models, schemas

router = APIRouter(tags=["Projects"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------- Projects ----------

@router.post("/projects", response_model=schemas.ProjectOut)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new = models.Project(
        title=project.title,
        description=project.description,
        owner_id=current_user.id
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.get("/projects", response_model=List[schemas.ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Project).filter(
        models.Project.owner_id == current_user.id
    ).all()


@router.put("/projects/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: int,
    data: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    proj = db.query(models.Project).filter_by(
        id=project_id, owner_id=current_user.id
    ).first()
    if not proj:
        raise HTTPException(404, "Project not found")
    proj.title, proj.description = data.title, data.description
    db.commit()
    db.refresh(proj)
    return proj


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    proj = db.query(models.Project).filter_by(
        id=project_id, owner_id=current_user.id
    ).first()
    if not proj:
        raise HTTPException(404, "Project not found")
    db.delete(proj)
    db.commit()
    return {"message": "Project deleted"}


# ---------- Task Endpoints (single source) ----------

@router.post("/projects/{project_id}/tasks",
             response_model=schemas.TaskOut)
def create_task(
    project_id: int,
    title: str = Form(...),
    description: str = Form(""),
    status: models.Status = Form(models.Status.PENDING),
    due_date: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(404, "Project not found")

    due = datetime.fromisoformat(due_date) if due_date else None
    task = models.Task(
        title=title, description=description, status=status.value,
        due_date=due, project_id=project_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # optional file upload
    if file:
        stored_name = f"{uuid4()}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, stored_name)
        with open(filepath, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        attach = models.FileAttachment(
            filename=stored_name,
            filepath=filepath,
            task_id=task.id
        )
        db.add(attach)
        db.commit()
    db.refresh(task)
    return task


@router.get("/projects/{project_id}/tasks", response_model=List[schemas.TaskOut])
def list_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get tasks only for this user's project
    project = db.query(models.Project).filter_by(id=project_id).first()
    if not project or project.owner_id != current_user.id:
        raise HTTPException(404, "Project not found or unauthorized")

    # Eager load attachments and comments->user to avoid N+1 lazy loads
    tasks = (
        db.query(models.Task)
        .options(
            joinedload(models.Task.attachments),
            joinedload(models.Task.comments).joinedload(models.Comment.user)
        )
        .filter_by(project_id=project_id)
        .all()
    )

    task_outputs = []
    for task in tasks:
        task_outputs.append(schemas.TaskOut(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            due_date=task.due_date,
            attachments=task.attachments,
            comments=[
                schemas.CommentOut(
                    id=c.id,
                    content=c.content,
                    timestamp=c.timestamp,
                    user_name=c.user.name  # ✅ Explicitly include user_name
                )
                for c in task.comments
            ]
        ))

    return task_outputs
