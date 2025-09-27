"""routers/assistant.py – AI Assistant endpoints backed by Gemini.

Gracefully returns 503 if GEMINI_API_KEY is missing so the app keeps running.
Maintains simple per-user in-memory conversation history.
"""

import os
import traceback
import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv
from ai.history_manager import HistoryManager

load_dotenv()

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

# Single process-local history manager instance
history = HistoryManager()

# Optional system prompt to make the bot TeamSync-aware. We'll send this via
# the API's systemInstruction field rather than as a chat message.
SYSTEM_PROMPT = (
    "You are TeamSync AI Assistant. You help teams with project management, tasks, and communication. "
    "Be concise, clear, and professional in responses."
)


class ChatRequest(BaseModel):
    user_id: str
    message: str


@router.post("/chat")
async def chat(payload: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")
    if not api_key:
        # Service not configured – don't hard-fail the whole app
        raise HTTPException(status_code=503, detail="AI is not configured on this deployment.")

    # Add user message to history and prepare conversation
    history.add_message(payload.user_id, "user", payload.message)
    conversation = history.get_history(payload.user_id)

    headers = {"Content-Type": "application/json"}
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": conversation,
    }

    try:
        print(f"[AI] Sending to Gemini: {payload.message[:50]}...")
        async with httpx.AsyncClient(timeout=90.0) as client:
            res = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                params={"key": api_key},
                headers=headers,
                json=body,
            )
        print("[HTTP] Status Code:", res.status_code)
        if res.status_code != 200:
            print("[ERROR] Gemini Error:", res.text)
            raise HTTPException(status_code=res.status_code, detail=f"Gemini Error: {res.text}")
        data = res.json()
        try:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            print("[ERROR] Error parsing Gemini response:", data)
            raise HTTPException(status_code=500, detail="Could not parse AI response.")
        print(f"[AI] Gemini Reply: {reply[:100]}...")
        # Save assistant reply to history
        history.add_message(payload.user_id, "model", reply)
        return {"reply": reply, "history": conversation}
    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] Exception:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")


@router.post("/reset")
async def reset_history(user_id: str = Query(..., description="User ID to clear history for")):
    """Clear history for a user (like a /reset button)."""
    history.clear_history(user_id)
    return {"detail": f"History cleared for user {user_id}"}
