
import pandas as pd
from pathlib import Path

# MacBook üzerinde ölçtüğümüz gerçek Docker süreleri
measurements = pd.read_csv(
    "data/benchmarks/docker_runtime.csv"
)

# Önceki deneyden yalnızca tarihleri alıyoruz.
# Bu, 2025 karbon verileriyle geriye dönük test içindir.
old_jobs = pd.read_csv("data/jobs_stress_fargate.csv")

images = {
    "small": "greenpipeline-worker:v1",
    "large": "greenpipeline-worker:v2"
}

jobs = []

for i, (workload, image) in enumerate(images.items()):
    sample = measurements[
        measurements["workload"] == workload
    ]

    # Ölçülen en uzun yerel süre
    measured_max = sample["duration_seconds"].max()

    # İlk test için %20 süre güvenlik payı
    estimated_seconds = measured_max * 1.20

    arrival = pd.to_datetime(
        old_jobs.iloc[i]["arrival_time"],
        utc=True
    )

    duration = pd.Timedelta(seconds=estimated_seconds)

    # Örnek SLA: tahmini süre + 5 dakika ek süre
    deadline = arrival + duration + pd.Timedelta(
        minutes=5
    )

    jobs.append({
        "job_id": i + 101,
        "image": image,
        "workload": workload,
        "arrival_time": arrival.isoformat(),
        "duration_min": estimated_seconds / 60,
        "deadline": deadline.isoformat(),
        "cpu": 0.25,
        "memory_gb": 0.5,
        "data_size_gb": 0.0,
        "data_region": "eu-central-1",
        "measured_max_seconds": measured_max,
        "duration_source": "local_docker_benchmark"
    })

Path("data").mkdir(exist_ok=True)

df = pd.DataFrame(jobs)
df.to_csv("data/measured_jobs.csv", index=False)

print("\nÖLÇÜME DAYALI GÖREV PROFİLLERİ")

print(df[[
    "job_id",
    "workload",
    "image",
    "measured_max_seconds",
    "duration_min"
]].to_string(index=False))

print("\nKaydedildi: data/measured_jobs.csv")
