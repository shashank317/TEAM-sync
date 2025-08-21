"""
main.py – FastAPI app startup
"""
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.openapi.utils import get_openapi
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


from models import Base
from database import engine
from auth import router as auth_router
from routers import (
    users, projects, tasks, comments, members,
    analytics
)
from routers import assistant



# ---------- Load environment ----------
load_dotenv()
assert os.getenv("GEMINI_API_KEY")," Missing GEMINI_API_KEY in .env file"

# ---------- App & DB ----------
 
app = FastAPI()

# ---------- Static & Template Mount ----------
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# ---------- Routers ----------
app.include_router(auth_router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(comments.router)
app.include_router(members.router)
app.include_router(assistant.router)
app.include_router(analytics.router)
# ---------- Custom Swagger with JWT Bearer ----------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="TeamSync API",
        version="2.0.0",
        description="Refactored backend with JWT auth",
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in schema["paths"].values():
        for method in path.values():
            method.setdefault("security", []).append({"BearerAuth": []})
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

# ---------- Frontend HTML Pages ----------
# ---------- Frontend HTML Pages ----------
@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    return templates.TemplateResponse("tasks.html", {"request": request})

@app.get("/members", response_class=HTMLResponse)
async def members_page(request: Request):
    return templates.TemplateResponse("members.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})