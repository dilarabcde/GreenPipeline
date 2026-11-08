
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("data/greenpipeline.db")


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = connect()
    try:
        with db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS job_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    image TEXT NOT NULL,
                    selected_region TEXT,
                    status TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    actual_runtime_seconds REAL,
                    error_message TEXT
                )
            """)
    finally:
        db.close()


def create_run(job_id, image, region):
    db = connect()
    try:
        with db:
            cursor = db.execute("""
                INSERT INTO job_runs (
                    job_id, image, selected_region,
                    status, environment, created_at
                )
                VALUES (?, ?, ?, 'Pending', 'local_docker', ?)
            """, (job_id, image, region, now_utc()))

            return cursor.lastrowid
    finally:
        db.close()


def update_run(run_id, status, runtime=None, error=None):
    db = connect()
    try:
        with db:
            if status == "Running":
                db.execute("""
                    UPDATE job_runs
                    SET status = ?, started_at = ?
                    WHERE run_id = ?
                """, (status, now_utc(), run_id))

            else:
                db.execute("""
                    UPDATE job_runs
                    SET status = ?,
                        finished_at = ?,
                        actual_runtime_seconds = ?,
                        error_message = ?
                    WHERE run_id = ?
                """, (
                    status, now_utc(),
                    runtime, error, run_id
                ))
    finally:
        db.close()


def get_run(run_id):
    db = connect()
    try:
        row = db.execute(
            "SELECT * FROM job_runs WHERE run_id = ?",
            (run_id,)
        ).fetchone()

        return dict(row) if row else None
    finally:
        db.close()


init_db()
