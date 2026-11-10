
import pandas as pd
from pathlib import Path

# Gercek Docker olcumleri
measurements = pd.read_csv(
    "data/benchmarks/real_docker_runtime_limited.csv"
)

input_file = Path("data/input/owid_energy.csv")

# Ilk 20 olcum: sure tahmini
train = measurements["runtime_seconds"].iloc[:20]

# Son 10 olcum: dogrulama
test = measurements["runtime_seconds"].iloc[20:]

p95 = train.quantile(0.95)

profile = {
    "workload": "owid_energy_processing",
    "image": "greenpipeline-external:v1",
    "input_file": input_file.name,
    "input_size_bytes": input_file.stat().st_size,
    "estimated_runtime_seconds": round(p95, 4),
    "duration_min": p95 / 60,
    "prediction_method": "P95",
    "measurement_source": "local_docker",
    "training_samples": len(train),
    "test_samples": len(test),
    "test_successful": int((test <= p95).sum()),
    "cpu_limit": 0.5,
    "memory_limit_mb": 512,
    "safety_margin_pct": 50,
    "planning_runtime_seconds": round(p95 * 1.50, 4)
}

df = pd.DataFrame([profile])

df.to_csv(
    "data/benchmarks/owid_workload_profile.csv",
    index=False
)

print("\nGREENPIPELINE - OWID GOREV PROFILI")
print(df.to_string(index=False))
