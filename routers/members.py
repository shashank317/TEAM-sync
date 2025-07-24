"""
routers/members.py – member management scoped to a project
"""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from pydantic import BaseModel

from database import get_db
from models import Project, ProjectMember, User
from auth import get_current_user, SECRET_KEY, ALGORITHM

router = APIRouter(
    prefix="/projects/{project_id}",
    tags=["Members"]
)

INVITE_EXPIRE_MIN = 60 * 24  # 1 day


# ---------- Schemas ----------

class MemberAdd(BaseModel):
    user_id: int
    role: str


class MemberUpdate(BaseModel):
    role: str


class MemberOut(BaseModel):
    user_id: int
    name: str
    email: str
    role: str


# ---------- Helpers ----------

def _project_owned(project_id: int, db, user: User) -> Project:
    proj = db.query(Project).filter(
        Project.id == project_id
    ).first()
    if not proj:
        raise HTTPException(404, "Project not found")
    if proj.owner_id != user.id:
        raise HTTPException(403, "Forbidden")
    return proj


# ---------- Endpoints ----------

@router.post("/members", response_model=MemberOut)
def add_member(
    project_id: int,
    payload: MemberAdd,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    proj = _project_owned(project_id, db, current_user)
    if db.query(ProjectMember).filter_by(
        project_id=project_id, user_id=payload.user_id
    ).first():
        raise HTTPException(400, "User already a member")
    user = db.query(User).filter_by(id=payload.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    mem = ProjectMember(
        user_id=payload.user_id,
        project_id=project_id,
        role=payload.role
    )
    db.add(mem)
    db.commit()
    return MemberOut(
        user_id=user.id, name=user.name, email=user.email, role=mem.role
    )


@router.get("/members", response_model=List[MemberOut])
def list_members(
    project_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    proj = _project_owned(project_id, db, current_user)
    rows = db.query(ProjectMember, User).join(
        User, ProjectMember.user_id == User.id
    ).filter(ProjectMember.project_id == project_id).all()
    return [
        MemberOut(user_id=u.id, name=u.name, email=u.email, role=m.role)
        for m, u in rows
    ]


@router.put("/members/{user_id}", response_model=MemberOut)
def update_member(
    project_id: int,
    user_id: int,
    payload: MemberUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _project_owned(project_id, db, current_user)
    mem = db.query(ProjectMember).filter_by(
        project_id=project_id, user_id=user_id
    ).first()
    if not mem:
        raise HTTPException(404, "Member not found")
    mem.role = payload.role
    db.commit()
    user = db.query(User).filter_by(id=user_id).first()
    return MemberOut(
        user_id=user.id, name=user.name, email=user.email, role=mem.role
    )


@router.delete("/members/{user_id}")
def delete_member(
    project_id: int,
    user_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _project_owned(project_id, db, current_user)
    mem = db.query(ProjectMember).filter_by(
        project_id=project_id, user_id=user_id
    ).first()
    if not mem:
        raise HTTPException(404, "Member not found")
    db.delete(mem)
    db.commit()
    return {"message": "Member removed"}


@router.get("/members/invite-link")
def invite_link(
    project_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _project_owned(project_id, db, current_user)
    exp = datetime.utcnow() + timedelta(minutes=INVITE_EXPIRE_MIN)
    token = jwt.encode(
        {"project_id": project_id, "exp": exp},
        SECRET_KEY, algorithm=ALGORITHM
    )
    link = f"http://localhost:8000/projects/{project_id}/members/join?token={token}"
    return {"invite_link": link}


@router.post("/members/join")
def join_via_token(
    project_id: int,
    token: str,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("project_id") != project_id:
            raise JWTError()
    except JWTError:
        raise HTTPException(400, "Invalid or expired invite")
    if db.query(ProjectMember).filter_by(
        project_id=project_id, user_id=current_user.id
    ).first():
        return {"message": "Already a member"}
    db.add(ProjectMember(
        user_id=current_user.id,
        project_id=project_id,
        role="member"
    ))
    db.commit()
    return {"message": "Joined project"}
