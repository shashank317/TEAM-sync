"""
routers/analytics.py – single source for project analytics
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models

router = APIRouter(prefix="/projects/{project_id}", tags=["Analytics"])


@router.get("/analytics")
def project_analytics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Ownership or membership check
    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()
    if not project:
        raise HTTPException(404, "Project not found")

    if project.owner_id != current_user.id and \
       not any(m.user_id == current_user.id for m in project.members):
        raise HTTPException(403, "Not authorized")

    # Count tasks by status
    counts = {s.value: 0 for s in models.Status}
    tasks = db.query(models.Task).filter(
        models.Task.project_id == project_id
    ).all()
    for t in tasks:
        counts[t.status] += 1

    return counts
