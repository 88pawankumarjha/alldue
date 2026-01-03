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
