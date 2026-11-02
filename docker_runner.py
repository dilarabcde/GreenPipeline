
import subprocess
import time
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from decision_engine import load_carbon_data, schedule_job

IMAGE = "greenpipeline-worker:v2"

# Fargate uyumlu görev veri setini kullan
jobs = pd.read_csv("data/jobs_stress_fargate.csv")
carbon_data = load_carbon_data()

# İlk görevi seç
job = jobs.iloc[0]

decision = schedule_job(job, carbon_data)

if decision is None:
    print("Görev için uygun zamanlama bulunamadı.")

else:
    print("\nGREENPIPELINE KARARI")
    print("Görev ID:", job["job_id"])
    print("Seçilen bölge:", decision["region"])
    print("Planlanan zaman:", decision["start"])
    print("Tahmini maliyet:", round(decision["cost_usd"], 4))
    print("Tahmini işlem emisyonu:", round(decision["carbon_g"], 4))

    print("\nYEREL DOCKER TESTİ BAŞLIYOR")
    print("Not: AWS bölgesi seçimi yalnızca simülasyondur.")

    started_at = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()

    process = subprocess.run(
        ["docker", "run", "--rm", IMAGE],
        capture_output=True,
        text=True
    )

    elapsed = time.perf_counter() - start

    print(process.stdout)

    if process.stderr:
        print(process.stderr)

    success = process.returncode == 0

    result = {
        "job_id": int(job["job_id"]),
        "image": IMAGE,
        "simulated_region": decision["region"],
        "simulated_start": str(decision["start"]),
        "local_started_at": started_at,
        "actual_runtime_seconds": round(elapsed, 4),
        "success": success
    }

    Path("data/benchmarks").mkdir(
        parents=True, exist_ok=True
    )

    output = "data/benchmarks/runner_result.json"

    with open(output, "w") as file:
        json.dump(result, file, indent=4)

    print("\nDOCKER RUNNER SONUCU")
    print("Başarılı:", success)
    print("Gerçek yerel süre:", round(elapsed, 4), "sn")
    print("Sonuç dosyası:", output)
