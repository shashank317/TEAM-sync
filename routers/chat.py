"""
routers/chat.py – WebSocket chat with JWT auth via query param

Endpoint: /chat/ws/{room_id}?token=...  (room_id can be a project id)

Auth: Accepts JWT signed with SECRET_KEY (HS256). Supports either claim:
 - user_id: int (our API tokens)
 - sub: str/int (common JWT subject field)

If room_id corresponds to a project, only owner or members can join.
"""

from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from auth import SECRET_KEY, ALGORITHM
from database import get_db
import models


router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        # room_id -> set of websockets
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, room_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self.rooms.setdefault(room_id, set()).add(ws)

    def disconnect(self, room_id: str, ws: WebSocket) -> None:
        room = self.rooms.get(room_id)
        if room and ws in room:
            room.remove(ws)
            if not room:
                self.rooms.pop(room_id, None)

    async def broadcast(self, room_id: str, message: dict) -> None:
        room = self.rooms.get(room_id)
        if not room:
            return
        for ws in list(room):
            try:
                await ws.send_json(message)
            except Exception:
                # Drop dead connections
                self.disconnect(room_id, ws)


manager = ConnectionManager()


def _decode_token(token: str) -> int:
    """Decode JWT and return user id (supports 'user_id' or 'sub')."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise
    uid = payload.get("user_id")
    if uid is None:
        uid = payload.get("sub")
    if uid is None:
        raise JWTError("Missing user claim")
    try:
        return int(uid)
    except (TypeError, ValueError):
        # If it's not an int, that's fine but we can't map to DB user
        # We'll raise to enforce a proper user id
        raise JWTError("Invalid user id claim")


async def _authorize_project_access(db: Session, project_id: int, user_id: int) -> bool:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        return False
    if project.owner_id == user_id:
        return True
    return db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user_id
    ).first() is not None


@router.websocket("/chat/ws/{room_id}")
async def chat_ws(websocket: WebSocket, room_id: str):
    # Expect token in query params
    token = websocket.query_params.get("token")
    if not token:
        # Per spec, reject handshake by closing with policy violation
        await websocket.close(code=1008)
        return

    # Validate token and user
    try:
        user_id = _decode_token(token)
    except JWTError:
        await websocket.close(code=1008)
        return

    # Optional: authorize project-based room access if room_id is an int
    db = next(get_db())
    try:
        if room_id.isdigit():
            allowed = await _authorize_project_access(db, int(room_id), user_id)
            if not allowed:
                await websocket.close(code=1008)
                return
    finally:
        db.close()

    # Accept and manage connection
    await manager.connect(room_id, websocket)
    await manager.broadcast(room_id, {"type": "join", "user_id": user_id})
    try:
        while True:
            data = await websocket.receive_json()
            # Minimal relay; clients can send {"message": "..."}
            await manager.broadcast(room_id, {
                "type": "message",
                "user_id": user_id,
                **({"message": data.get("message")} if isinstance(data, dict) else {})
            })
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(room_id, websocket)
        await manager.broadcast(room_id, {"type": "leave", "user_id": user_id})
