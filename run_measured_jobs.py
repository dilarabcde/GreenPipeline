
import pandas as pd
import subprocess
import time
from pathlib import Path

from decision_engine import load_carbon_data, schedule_job

jobs = pd.read_csv("data/measured_jobs.csv")
carbon_data = load_carbon_data()

results = []

for _, job in jobs.iterrows():
    print(f"\n--- GÖREV {job['job_id']} ---")

    # Zamanlayıcının kararı
    decision = schedule_job(job, carbon_data)

    if decision is None:
        print("Uygun plan bulunamadı.")
        continue

    image = job["image"]

    print("Docker imajı:", image)
    print("Simülasyonda seçilen bölge:", decision["region"])
    print("Simülasyonda seçilen saat:", decision["start"])

    # Geçmiş tarihli planı beklemiyoruz.
    # Docker görevini şimdi, yerelde çalıştırıyoruz.
    start = time.perf_counter()

    process = subprocess.run(
        ["docker", "run", "--rm", image],
        capture_output=True,
        text=True
    )

    actual_seconds = time.perf_counter() - start
    estimated_seconds = float(job["duration_min"]) * 60

    error_seconds = actual_seconds - estimated_seconds

    results.append({
        "job_id": int(job["job_id"]),
        "image": image,
        "simulated_region": decision["region"],
        "estimated_seconds": round(estimated_seconds, 4),
        "actual_seconds": round(actual_seconds, 4),
        "error_seconds": round(error_seconds, 4),
        "success": process.returncode == 0
    })

    print("Tahmini süre:", round(estimated_seconds, 3), "sn")
    print("Gerçek süre:", round(actual_seconds, 3), "sn")
    print("Tahmin hatası:", round(error_seconds, 3), "sn")
    print("Başarılı:", process.returncode == 0)

    if process.returncode != 0:
        print("Hata:", process.stderr)

Path("data/benchmarks").mkdir(
    parents=True, exist_ok=True
)

df = pd.DataFrame(results)

df.to_csv(
    "data/benchmarks/measured_job_results.csv",
    index=False
)

print("\nKARŞILAŞTIRMA")
print(df.to_string(index=False))
