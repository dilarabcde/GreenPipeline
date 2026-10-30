
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

# Karbon verilerimiz 2025 yılına ait.
start = datetime(2025, 1, 1)
jobs = []

for i in range(1, 101):
    arrival = start + timedelta(
        minutes=random.randint(0, 364 * 24 * 60)
    )

    duration = random.randint(5, 180)
    slack = random.randint(30, 360)

    deadline = arrival + timedelta(
        minutes=duration + slack
    )

    # Görevin işleyeceği veri miktarı (GB)
    data_size = random.choice([
        0.1, 0.5, 1, 5, 10, 20, 50, 100
    ])

    jobs.append({
        "job_id": i,
        "arrival_time": arrival.isoformat(),
        "duration_min": duration,
        "deadline": deadline.isoformat(),
        "cpu": random.choice([0.25, 0.5, 1.0]),
        "memory_gb": random.choice([0.5, 1.0, 2.0]),
        "data_size_gb": data_size,
        "data_region": "eu-central-1"
    })

Path("data").mkdir(exist_ok=True)

with open("data/jobs.csv", "w", newline="") as file:
    writer = csv.DictWriter(
        file, fieldnames=jobs[0].keys()
    )
    writer.writeheader()
    writer.writerows(jobs)

print("100 görev oluşturuldu!")
print("Veri boyutları ve veri konumları eklendi.")
