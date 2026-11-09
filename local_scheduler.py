
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from database import connect, update_run


def now_utc():
    return datetime.now(timezone.utc).isoformat()


# Mevcut SQLite tablosuna zamanlama alanı ekle.

def prepare_database():
    db = connect()
    try:
        columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(job_runs)")
        }

        new_columns = {
            "scheduled_at": "TEXT",
            "deadline_at": "TEXT",
            "deadline_met": "INTEGER",
            "lateness_seconds": "REAL"
        }

        with db:
            for name, column_type in new_columns.items():
                if name not in columns:
                    db.execute(
                        f"ALTER TABLE job_runs "
                        f"ADD COLUMN {name} {column_type}"
                    )
    finally:
        db.close()


prepare_database()



def queue_job(job_id, image, delay_seconds, deadline_seconds):
    now = datetime.now(timezone.utc)

    scheduled_at = (
        now + timedelta(seconds=delay_seconds)
    ).isoformat()

    deadline_at = (
        now + timedelta(seconds=deadline_seconds)
    ).isoformat()

    db = connect()
    try:
        with db:
            cursor = db.execute("""
                INSERT INTO job_runs (
                    job_id, image, selected_region,
                    status, environment, created_at,
                    scheduled_at, deadline_at
                )
                VALUES (
                    ?, ?, NULL, 'Scheduled',
                    'local_docker', ?, ?, ?
                )
            """, (
                job_id, image, now.isoformat(),
                scheduled_at, deadline_at
            ))

            run_id = cursor.lastrowid
    finally:
        db.close()

    return {
        "run_id": run_id,
        "job_id": job_id,
        "status": "Scheduled",
        "scheduled_at": scheduled_at,
        "deadline_at": deadline_at,
        "environment": "local_docker"
    }


def claim_due_job():
    db = connect()
    try:
        db.execute("BEGIN IMMEDIATE")

        row = db.execute("""
            SELECT run_id, job_id, image
            FROM job_runs
            WHERE status = 'Scheduled'
              AND scheduled_at <= ?
            ORDER BY scheduled_at, run_id
            LIMIT 1
        """, (now_utc(),)).fetchone()

        if row is None:
            db.commit()
            return None

        db.execute("""
            UPDATE job_runs
            SET status = 'Running', started_at = ?
            WHERE run_id = ?
        """, (now_utc(), row["run_id"]))

        db.commit()
        return dict(row)
    finally:
        db.close()


def record_deadline_result(run_id):
    db = connect()

    try:
        row = db.execute("""
            SELECT status, finished_at, deadline_at
            FROM job_runs
            WHERE run_id = ?
        """, (run_id,)).fetchone()

        if not row or not row["deadline_at"] or not row["finished_at"]:
            return

        finished = datetime.fromisoformat(row["finished_at"])
        deadline = datetime.fromisoformat(row["deadline_at"])

        lateness = (finished - deadline).total_seconds()

        deadline_met = int(
            row["status"] == "Completed"
            and lateness <= 0
        )

        with db:
            db.execute("""
                UPDATE job_runs
                SET deadline_met = ?,
                    lateness_seconds = ?
                WHERE run_id = ?
            """, (
                deadline_met,
                round(lateness, 4),
                run_id
            ))

    finally:
        db.close()



def execute_job(job):
    run_id = job["run_id"]
    image = job["image"]
    container_name = f"greenpipeline-run-{run_id}"

    print(f"\nGörev başlıyor: run_id={run_id}", flush=True)

    started = time.perf_counter()

    try:
        allowed_images = {
            "greenpipeline-worker:v1",
            "greenpipeline-worker:v2",
            "greenpipeline-external:v1"
        }

        if image not in allowed_images:
            raise ValueError(f"Desteklenmeyen Docker imajı: {image}")

        command = [
            "docker", "run", "--rm",
            "--name", container_name,
            "--cpus", "0.5",
            "--memory", "512m"
        ]

        # OWID görevine gerçek CSV dosyasını bağla
        if image == "greenpipeline-external:v1":
            input_dir = (
                Path(__file__).resolve().parent
                / "data" / "input"
            )

            input_file = input_dir / "owid_energy.csv"

            if not input_file.is_file():
                raise FileNotFoundError(
                    f"OWID veri dosyası bulunamadı: {input_file}"
                )

            command.extend([
                "--mount",
                f"type=bind,source={input_dir},target=/input,readonly"
            ])

        command.append(image)

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60
        )

        elapsed = time.perf_counter() - started

        status = (
            "Completed" if process.returncode == 0
            else "Failed"
        )

        update_run(
            run_id,
            status,
            runtime=round(elapsed, 4),
            error=process.stderr[-1000:]
            if process.returncode != 0 else None
        )

        record_deadline_result(run_id)

        print(process.stdout[-1000:])
        print(f"Durum: {status}")
        print(f"Süre: {elapsed:.4f} saniye", flush=True)

    except Exception as error:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            timeout=10
        )

        update_run(
            run_id,
            "Failed",
            error=str(error)
        )

        record_deadline_result(run_id)

        print(
            f"Görev başarısız: {error}",
            flush=True
        )


if __name__ == "__main__":
    print("GreenPipeline Local Scheduler çalışıyor.")
    print("Planlanan görevler kontrol ediliyor...")

    try:
        while True:
            job = claim_due_job()

            if job is not None:
                execute_job(job)
            else:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nScheduler durduruldu.")
