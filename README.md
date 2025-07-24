# 🧠 TeamSync – Smart Project Management Tool

TeamSync is a full-featured project collaboration platform built with **FastAPI** and **Tailwind CSS**, designed for managing teams, tasks, files, and communication efficiently.

---

## 🚀 Features

- 🧑‍💼 **User Authentication**
  - JWT-based signup, login, and auto-login
  - Password reset & profile updates

- 📁 **Project & Task Management**
  - Create projects, add tasks with statuses (pending/in-progress/done)
  - Set due dates with visual color indicators (e.g., overdue, due today)
  - Assign tasks to members

- 📎 **File Attachments**
  - Upload and view files attached to tasks
  - Local `/uploads/` storage (S3 support planned)

- 💬 **Live Chat-style Comments**
  - Real-time styled threaded comments under each task

- 📊 **Analytics**
  - Task completion charts (pie + bar) using Chart.js

- 🤖 **AI Assistant**
  - Integrated AI Assistant powered by OpenRouter API
  - Chat with AI on the dashboard (working in dev, stable version deployed soon)

- 👥 **Member Management**
  - Add/remove/update project members and roles
  - Generate invite links to join projects

- 🌓 **Dark Mode**
  - Fully supported and toggleable per user

---

## 📦 Tech Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** HTML, TailwindCSS, Vanilla JS
- **Auth:** JWT
- **AI:** OpenRouter API
- **Charts:** Chart.js
- **ORM:** SQLAlchemy
- **Deployment Targets:** Render (first), AWS EC2 + S3 (next)

---

## ⚙️ Local Development Setup

```bash
git clone https://github.com/shashank317/TEAM-sync.git
cd TEAM-sync
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt



🌐 Deployment Status
Platform	Status
✅ Local	Working
⚠️ Render	Config in progress (fixing frontend path issues)
🚧 AWS	Planned


🛠️ Future Roadmap
✅ AI Assistant (via OpenRouter)

✅ File attachments per task

✅ Task due date logic & color UI

✅ Member invite via link

🚀 Migrate file uploads to AWS S3

🚀 Full deployment on Render or AWS

🎨 Move frontend to React (component-wise)

