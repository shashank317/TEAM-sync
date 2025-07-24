"""
routers/comments.py – comments endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models, schemas

router = APIRouter(tags=["Comments"])


@router.post("/tasks/{task_id}/comments", response_model=schemas.CommentOut)
def add_comment(
    task_id: int,
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.Task).join(models.Project).filter(
        models.Task.id == task_id,
        models.Project.owner_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(404, "Task not found or unauthorized")
    new = models.Comment(
        content=comment.content,
        task_id=task_id,
        user_id=current_user.id
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return schemas.CommentOut(
        id=new.id, content=new.content,
        timestamp=new.timestamp, user_name=current_user.name
    )


@router.get("/tasks/{task_id}/comments", response_model=List[schemas.CommentOut])
def list_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.Task).join(models.Project).filter(
        models.Task.id == task_id,
        models.Project.owner_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(404, "Task not found or unauthorized")

    comments = db.query(models.Comment).join(models.User).filter(
        models.Comment.task_id == task_id
    ).order_by(models.Comment.timestamp.asc()).all()

    return [
        schemas.CommentOut(
            id=c.id, content=c.content,
            timestamp=c.timestamp, user_name=c.user.name
        )
        for c in comments
    ]
