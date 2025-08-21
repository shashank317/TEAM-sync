# routers/assistant.py

import os
import traceback
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY missing. Check .env or environment variables.")

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty")

    headers = {
        "Content-Type": "application/json",
    }

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": payload.message
                    }
                ]
            }
        ]
    }

    try:
        print(f"📤 Sending to Gemini: {payload.message[:50]}...")

        async with httpx.AsyncClient(timeout=90.0) as client:
            res = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
                headers=headers,
                json=body
            )

        print("🔧 Status Code:", res.status_code)

        if res.status_code != 200:
            print("❌ Gemini Error:", res.text)
            raise HTTPException(status_code=res.status_code, detail=f"Gemini Error: {res.text}")

        response_data = res.json()
        
        # --- Safe response parsing ---
        try:
            reply = response_data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            print("❌ Error parsing Gemini response:", response_data)
            raise HTTPException(status_code=500, detail="Could not parse AI response.")

        print(f"🤖 Gemini Reply: {reply[:100]}...")
        return {"reply": reply}

    except Exception as e:
        print("❌ Exception:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")
