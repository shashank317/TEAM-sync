"""
main.py – FastAPI app startup
"""
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.openapi.utils import get_openapi
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


from models import Base
from database import engine, get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from auth import router as auth_router
from routers import (
    users, projects, tasks, comments, members,
    analytics, chat
)
from routers import assistant



# ---------- Load environment ----------
load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
    # Non-fatal warning; only features needing the key will fail later.
    print("[WARN] GEMINI_API_KEY not set – assistant features may be limited.")

# ---------- App & DB ----------
 
app = FastAPI()

# Simple timing middleware (dev) to inspect slow endpoints locally
@app.middleware("http")
async def add_process_time_header(request, call_next):
    from time import perf_counter
    start = perf_counter()
    response = await call_next(request)
    duration = (perf_counter() - start) * 1000
    # Only attach for JSON/HTML (skip static) to keep noise low
    if request.url.path.startswith(('/projects','/tasks','/dashboard','/members','/analytics','/profile')):
        response.headers['X-Process-Time-ms'] = f"{duration:.1f}"
    return response

# Log DB URL (without password) at startup for diagnostics
@app.on_event("startup")
async def startup_banner():
    try:
        safe_url = engine.url.render_as_string(hide_password=True)
        print(f"[STARTUP] Using database: {safe_url}")
        # Auto-create tables for local sqlite OR when explicitly requested
        backend = engine.url.get_backend_name()
        if backend.startswith('sqlite') or os.getenv('MIGRATE_ON_START') == '1':
            from models import Base  # local import to avoid circulars
            Base.metadata.create_all(bind=engine)
            print("[STARTUP] Ensured database schema (auto create_all).")
    except Exception as e:
        print(f"[STARTUP][WARN] Startup tasks failed: {e}")

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
app.include_router(chat.router)

# ---------- Health / Diagnostics ----------
@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": engine.url.render_as_string(hide_password=True)}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB error: {e}")
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
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/reset", response_class=HTMLResponse)
async def reset(request: Request):
    return templates.TemplateResponse("reset.html", {"request": request})

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

# Added missing profile page route so sidebar /profile navigation works
@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})