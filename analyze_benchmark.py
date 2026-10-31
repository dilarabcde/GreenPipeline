
import pandas as pd

df = pd.read_csv("data/benchmarks/docker_runtime.csv")

summary = df.groupby("workload")["duration_seconds"].agg(
    ["count", "mean", "std", "min", "max"]
)

print("\nDOCKER PERFORMANS SONUÇLARI")
print(summary.round(4).to_string())

print("\nTÜM ÖLÇÜMLER")
print(df[["workload", "run", "duration_seconds"]].to_string(index=False))

summary.to_csv("data/benchmarks/docker_summary.csv")

print("\nÖzet kaydedildi.")
