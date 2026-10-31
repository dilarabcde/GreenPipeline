
import csv
import subprocess
import time
from pathlib import Path

IMAGES = {
    "small": "greenpipeline-worker:v1",
    "large": "greenpipeline-worker:v2"
}

REPEATS = 5
results = []

for workload, image in IMAGES.items():
    for run in range(1, REPEATS + 1):
        print(f"Çalışıyor: {workload}, deneme {run}")

        start = time.perf_counter()

        process = subprocess.run(
            ["docker", "run", "--rm", image],
            capture_output=True,
            text=True
        )

        elapsed = time.perf_counter() - start

        if process.returncode != 0:
            raise RuntimeError(process.stderr)

        results.append({
            "workload": workload,
            "image": image,
            "run": run,
            "duration_seconds": round(elapsed, 4),
            "success": True
        })

Path("data/benchmarks").mkdir(
    parents=True, exist_ok=True
)

output = "data/benchmarks/docker_runtime.csv"

with open(output, "w", newline="") as file:
    writer = csv.DictWriter(
        file, fieldnames=results[0].keys()
    )
    writer.writeheader()
    writer.writerows(results)

print("\nÖlçümler kaydedildi:", output)
