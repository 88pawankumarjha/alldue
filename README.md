# AllDue — Minimal Reminders App

Simple FastAPI app to track reminders and deadlines in a unified view.

Run locally:

1. Create and activate a virtualenv (recommended):

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # PowerShell

2. Install deps:

   pip install -r requirements.txt

3. Start the app:

   uvicorn main:app --reload

Open http://127.0.0.1:8000/ and add reminders.

Guiding constraints: manual-first, lightweight, no auth, SQLite storage.

## Deployment (current)

- Repo: https://github.com/88pawankumarjha/alldue
- Deployed to: http://43.204.152.235 (ensure EC2 security group allows inbound HTTP (port 80)).

Basic server steps (already performed):
1. apt update && apt install -y python3-venv python3-pip nginx git
2. git clone https://github.com/88pawankumarjha/alldue.git
3. python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
4. Create systemd unit to run uvicorn and configure Nginx as reverse proxy

Note: For HTTPS, add a domain and run certbot with the nginx plugin.
