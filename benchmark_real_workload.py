
import csv
import subprocess
import time
import statistics
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent

INPUT_FILE = ROOT / "data/input/owid_energy.csv"
OUTPUT_FILE = ROOT / "data/benchmarks/real_docker_runtime_validation.csv"

IMAGE = "greenpipeline-external:v1"
REPETITIONS = 20

if not INPUT_FILE.exists():
    raise SystemExit(
        f"Veri dosyasi bulunamadi: {INPUT_FILE}"
    )

OUTPUT_FILE.parent.mkdir(
    parents=True, exist_ok=True
)

records = []

for run_number in range(1, REPETITIONS + 1):

    command = [
        "docker", "run", "--rm",
        "--cpus", "0.5",
        "--memory", "512m",
        "--mount",
        f"type=bind,source={INPUT_FILE.parent},target=/input,readonly",
        IMAGE
    ]

    start = time.perf_counter()

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=120
    )

    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        raise RuntimeError(
            f"Docker hatasi:\n{result.stderr}"
        )

    records.append({
        "run": run_number,
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "image": IMAGE,
        "input_file": INPUT_FILE.name,
        "input_size_bytes": INPUT_FILE.stat().st_size,
        "runtime_seconds": round(elapsed, 4)
    })

    print(
        f"Calistirma {run_number}: "
        f"{elapsed:.4f} saniye"
    )

with OUTPUT_FILE.open("w", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=records[0].keys()
    )
    writer.writeheader()
    writer.writerows(records)

times = [
    record["runtime_seconds"]
    for record in records
]

print("\nGERCEK VERI - DOCKER BENCHMARK")
print("Tekrar sayisi:", REPETITIONS)
print("Ortalama:", round(statistics.mean(times), 4), "s")
print("Medyan:", round(statistics.median(times), 4), "s")
print("Minimum:", round(min(times), 4), "s")
print("Maksimum:", round(max(times), 4), "s")

print("\nSonuclar kaydedildi:")
print(OUTPUT_FILE)
