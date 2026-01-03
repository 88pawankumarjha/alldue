"""AllDue — minimal FastAPI app with SQLite backing."""
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import date, datetime
import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "reminders.db")

app = FastAPI()
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            deadline TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_reminder(title: str, source: str, deadline: str):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO reminders (title, source, deadline, created_at) VALUES (?, ?, ?, ?)",
        (title, source, deadline, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_all_reminders():
    conn = get_db_connection()
    cur = conn.execute("SELECT * FROM reminders ORDER BY deadline ASC")
    rows = cur.fetchall()
    conn.close()

    today = date.today()
    out = []
    for r in rows:
        row_deadline = None
        row_class = "upcoming"
        try:
            row_deadline = date.fromisoformat(r["deadline"])
            if row_deadline < today:
                row_class = "overdue"
            elif row_deadline == today:
                row_class = "due-today"
        except Exception:
            row_deadline = None
            row_class = "upcoming"

        out.append({
            "id": r["id"],
            "title": r["title"],
            "source": r["source"],
            "deadline": r["deadline"],
            "row_class": row_class,
        })
    return out


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def index(request: Request):
    reminders = get_all_reminders()
    return templates.TemplateResponse("index.html", {"request": request, "reminders": reminders})


@app.post("/add")
def add(request: Request, title: str = Form(...), source: str = Form(...), deadline: str = Form(...)):
    # basic validation: ensure deadline is YYYY-MM-DD
    try:
        _ = date.fromisoformat(deadline)
    except Exception:
        # ignore invalid date, redirect back (could show message later)
        return RedirectResponse(url="/", status_code=303)

    add_reminder(title, source, deadline)
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
