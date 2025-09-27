# 🧠 TeamSync – Smart Project Management Tool

TeamSync is a full-featured project collaboration platform built with FastAPI. It includes projects, tasks, comments, file uploads, analytics, members, and an optional AI assistant.

---

## 🚀 Features

- Authentication: JWT (header and HTTP-only cookie), logout
- Projects & Tasks: CRUD, statuses (pending/in-progress/done), due dates
- Attachments: Upload per task to /uploads (local disk)
- Comments: Chat-style threaded comments under each task
- Analytics: Project charts with optional task panel (Chart.js)
- Members: Invite links and role management; members can view roster
- Dark, glass UI across dashboard and kanban
- Optional AI Assistant (Gemini) – gracefully disabled if not configured

---

## 📦 Tech Stack

- Backend: FastAPI, SQLAlchemy (2.x)
- DB: PostgreSQL (production) / SQLite (optional local fallback)
- Templating: Jinja2, TailwindCSS, Vanilla JS
- Charts: Chart.js
- Auth: jose/jwt + passlib/bcrypt

---

## ⚙️ Local Development

Windows (PowerShell or cmd):

```bat
git clone https://github.com/shashank317/TEAM-sync.git
cd TEAM-sync
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env  2>NUL
```

Set environment variables in .env (see below). To run:

```bat
set UVICORN_HOST=0.0.0.0
set UVICORN_PORT=8000
uvicorn main:app --host %UVICORN_HOST% --port %UVICORN_PORT%
```

Visit http://localhost:8000

---

## 🔧 Environment Variables

Database (choose ONE):

- DATABASE_URL=postgresql://user:pass@host:5432/dbname
  - Driver automatically normalized to postgresql+psycopg2 and sslmode=require for Render/Neon
- OR set USE_SQLITE=1 and optional SQLITE_PATH=sqlite:///./teamsync.db (local dev only)

Security/cookies:

- JWT_SECRET=change_me
- COOKIE_SECURE=1           (enable on HTTPS e.g., Render)
- COOKIE_SAMESITE=lax       (or none when needed for cross-site)

AI (optional):

- GEMINI_API_KEY=...        (omit to disable /ai routes; they return 503)

Other:

- SQL_ECHO=0                (set 1 to log SQL)
- MIGRATE_ON_START=0        (set 1 to auto create_all for SQLite)
- PRINT_DB_INFO=0           (set 1 to print DB URL on startup)

---

## 🗃️ Database & Migrations

Alembic is configured. For Postgres:

```bat
set DATABASE_URL=postgresql://user:pass@host:5432/db
alembic upgrade head
```

Render/Neon typically require sslmode=require; this is auto-added. You can override with DB_SSLMODE.

---

## 🧪 Smoke Test

After starting the app:

- GET /health/db should return {"status":"ok"}
- Create user via /auth/signup (also sets cookie)
- Create a project in /dashboard and add tasks in /tasks?id=<project_id>
- Uploads are saved in /uploads and served at /uploads/<stored_filename>

---

## ☁️ Deploy on Render

1) Create a Render PostgreSQL instance. Copy its external DATABASE_URL.
2) Create a new Web Service:
   - Build Command: pip install -r requirements.txt
   - Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
3) Add Environment Variables:
   - DATABASE_URL=<your value>
   - JWT_SECRET=<random-long-secret>
   - COOKIE_SECURE=1
   - COOKIE_SAMESITE=lax
   - GEMINI_API_KEY=<optional>
4) (Optional) Run Alembic migrate once via a Render job or shell: alembic upgrade head

Static mounts:

- The app serves /static and /uploads folders automatically. Ensure uploads/ exists (it will be created on first upload).

Note: Render’s disk is ephemeral. Uploaded files can be lost on redeploys or restarts. For production, configure S3 and update the upload logic accordingly (planned).

---

## � Known Issues & Fixes

- AI endpoint used to crash if GEMINI_API_KEY missing – fixed: now returns 503.
- Upload filenames are stored uniquely to avoid collisions; UI shows original name.
- Cookie flags are configurable for production. Set COOKIE_SECURE=1 on HTTPS.
- Project and Task analytics are protected by owner/member checks.

---

## 🛣️ Roadmap

- Team-wide activity feed persisted server-side
- Optional S3 storage for attachments
- Real-time updates for tasks/comments via WebSocket
- React front-end

---

## License

MIT



