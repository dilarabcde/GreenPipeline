
from functools import lru_cache

import subprocess
import time
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from decision_engine import load_carbon_data, schedule_job

app = FastAPI(
    title="GreenPipeline API",
    version="0.1.0"
)


class JobRequest(BaseModel):
    job_id: int


@lru_cache
def get_carbon_data():
    return load_carbon_data()


@app.get("/health")
def health():
    return {"status": "ok", "service": "GreenPipeline"}


@app.get("/jobs")
def list_jobs():
    jobs = pd.read_csv("data/measured_jobs.csv")

    return jobs[
        ["job_id", "workload", "image", "duration_min"]
    ].to_dict(orient="records")


@app.post("/jobs/plan")
def plan_job(request: JobRequest):
    jobs = pd.read_csv("data/measured_jobs.csv")
    matches = jobs[jobs["job_id"] == request.job_id]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail="Görev bulunamadı"
        )

    job = matches.iloc[0]

    decision = schedule_job(job, get_carbon_data())

    if decision is None:
        raise HTTPException(
            status_code=422,
            detail="Deadline ve bütçeye uygun plan yok"
        )

    return {
        "job_id": int(job["job_id"]),
        "image": str(job["image"]),
        "selected_region": decision["region"],
        "scheduled_start": str(decision["start"]),
        "estimated_cost_usd": round(
            float(decision["cost_usd"]), 6
        ),
        "estimated_carbon_g": round(
            float(decision["carbon_g"]), 4
        ),
        "execution_status": "simulation_only"
    }


@app.post("/jobs/run")
def run_job(request: JobRequest):
    jobs = pd.read_csv("data/measured_jobs.csv")
    matches = jobs[jobs["job_id"] == request.job_id]

    if matches.empty:
        raise HTTPException(404, "Görev bulunamadı")

    job = matches.iloc[0]
    image = str(job["image"])

    # Yalnızca önceden tanımladığımız imajlara izin ver
    allowed_images = {
        "greenpipeline-worker:v1",
        "greenpipeline-worker:v2"
    }

    if image not in allowed_images:
        raise HTTPException(400, "İzin verilmeyen Docker imajı")

    start = time.perf_counter()

    try:
        process = subprocess.run(
            [
                "docker", "run", "--rm",
                "--cpus", "0.5",
                "--memory", "512m",
                image
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Görev zaman aşımına uğradı")
    except OSError as error:
        raise HTTPException(503, f"Docker başlatılamadı: {error}")

    elapsed = time.perf_counter() - start

    return {
        "job_id": int(job["job_id"]),
        "image": image,
        "success": process.returncode == 0,
        "return_code": process.returncode,
        "actual_runtime_seconds": round(elapsed, 4),
        "output": process.stdout[-2000:],
        "error": process.stderr[-1000:],
        "execution_environment": "local_docker"
    }

from datetime import datetime, timezone


@app.post("/jobs/demo")
def demo_job(request: JobRequest):

    # 1. Geçmiş verilerle plan oluştur
    plan = plan_job(request)

    # 2. Gerçek Docker görevini şimdi, yerelde çalıştır
    execution = run_job(request)

    # 3. İki sonucu tek yanıtta birleştir
    return {
        "job_id": request.job_id,
        "mode": "historical_plan_local_execution",
        "plan": {
            "selected_region": plan["selected_region"],
            "scheduled_start": plan["scheduled_start"],
            "estimated_cost_usd": plan["estimated_cost_usd"],
            "estimated_carbon_g": plan["estimated_carbon_g"]
        },
        "execution": {
            "image": execution["image"],
            "success": execution["success"],
            "actual_runtime_seconds": (
                execution["actual_runtime_seconds"]
            ),
            "return_code": execution["return_code"],
            "environment": "local_docker",
            "completed_at_utc": (
                datetime.now(timezone.utc).isoformat()
            )
        },
        "note": (
            "Plan tarihi geçmiş simülasyondur. "
            "Docker görevi yerelde hemen çalıştırılmıştır. "
            "AWS bölgesi ve planlanan saat uygulanmamıştır."
        )
    }

from database import create_run, update_run, get_run


@app.post("/jobs/tracked-run")
def tracked_run(request: JobRequest):

    # 1. GreenPipeline planını oluştur
    plan = plan_job(request)

    # 2. SQLite'a Pending kaydı ekle
    run_id = create_run(
        request.job_id,
        plan["image"],
        plan["selected_region"]
    )

    # 3. Çalışıyor durumuna geçir
    update_run(run_id, "Running")

    try:
        # 4. Gerçek Docker görevini yerelde çalıştır
        execution = run_job(request)

        status = (
            "Completed"
            if execution["success"]
            else "Failed"
        )

        # 5. Sonucu veritabanına kaydet
        update_run(
            run_id,
            status,
            runtime=execution["actual_runtime_seconds"],
            error=execution["error"] if not execution["success"] else None
        )

    except Exception as error:
        update_run(
            run_id,
            "Failed",
            error=str(error)
        )
        raise

    return {
        "run_id": run_id,
        "job_id": request.job_id,
        "status": status,
        "selected_region": plan["selected_region"],
        "actual_runtime_seconds": execution["actual_runtime_seconds"],
        "execution_environment": "local_docker"
    }


@app.get("/runs/{run_id}")
def read_run(run_id: int):
    result = get_run(run_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Çalıştırma kaydı bulunamadı"
        )

    return result


from pydantic import Field
from local_scheduler import queue_job

class ScheduleRequest(BaseModel):
    job_id: int
    delay_seconds: int = Field(ge=5, le=300)
    deadline_seconds: int = Field(ge=1, le=600)

@app.post("/jobs/schedule-local")
def schedule_local(request: ScheduleRequest):

    jobs = pd.read_csv("data/measured_jobs.csv")
    matches = jobs[jobs["job_id"] == request.job_id]

    if matches.empty:
        raise HTTPException(404, "Görev bulunamadı")

    image = str(matches.iloc[0]["image"])

    allowed_images = {
        "greenpipeline-worker:v1",
        "greenpipeline-worker:v2"
    }

    if image not in allowed_images:
        raise HTTPException(
            400, "İzin verilmeyen Docker imajı"
        )

    return queue_job(
        request.job_id,
        image,
        request.delay_seconds,
        request.deadline_seconds
    )
