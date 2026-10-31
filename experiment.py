
import pandas as pd

from decision_engine import (
    load_carbon_data,
    schedule_job,
    estimate_emissions
)
from cost_model import calculate_total_cost

# Aynı görevleri bütün yöntemlerde kullanacağız
jobs = pd.read_csv("data/jobs_stress.csv")
carbon_data = load_carbon_data()


def run_baseline(job):
    """Görevi verinin bulunduğu bölgede hemen çalıştır."""
    region = job["data_region"]
    start = pd.to_datetime(job["arrival_time"], utc=True)
    deadline = pd.to_datetime(job["deadline"], utc=True)

    finish = start + pd.Timedelta(
        minutes=float(job["duration_min"])
    )

    _, _, cost = calculate_total_cost(job, region)

    carbon = estimate_emissions(
        job, region, start, carbon_data
    )

    return {
        "region": region,
        "cost_usd": cost,
        "carbon_g": carbon,
        "deadline_met": finish <= deadline
    }


results = []

for _, job in jobs.iterrows():

    baseline = run_baseline(job)

    # Karbon odaklı: bütçe sınırı yok
    carbon_only = schedule_job(
        job, carbon_data, max_cost_usd=float("inf")
    )

    # GreenPipeline: 0.25 dolar bütçe sınırı var
    greenpipeline = schedule_job(job, carbon_data)

    methods = {
        "Baseline": baseline,
        "Carbon-only": carbon_only,
        "GreenPipeline": greenpipeline
    }

    for method, decision in methods.items():

        if decision is None:
            results.append({
                "job_id": job["job_id"],
                "method": method,
                "region": "No feasible option",
                "cost_usd": None,
                "carbon_g": None,
                "deadline_met": False
            })
            continue

        # Zamanlayıcı uygun seçenekleri zaten
        # deadline koşuluna göre filtreliyor.
        deadline_met = (
            baseline["deadline_met"]
            if method == "Baseline"
            else True
        )

        results.append({
            "job_id": job["job_id"],
            "method": method,
            "region": decision["region"],
            "cost_usd": decision["cost_usd"],
            "carbon_g": decision["carbon_g"],
            "deadline_met": deadline_met
        })


df = pd.DataFrame(results)

summary = df.groupby("method").agg(
    total_jobs=("job_id", "count"),
    completed=("deadline_met", "sum"),
    total_cost=("cost_usd", "sum"),
    total_carbon=("carbon_g", "sum")
)

summary["missed_jobs"] = (
    summary["total_jobs"] - summary["completed"]
)

print("\nGREENPIPELINE DENEY SONUÇLARI")
print(summary.round(4).to_string())

print("\nBÖLGE DAĞILIMI")
print(pd.crosstab(df["method"], df["region"]))

df.to_csv("data/experiment_results.csv", index=False)
summary.to_csv("data/experiment_summary.csv")

print("\nDeney sonuçları kaydedildi.")
