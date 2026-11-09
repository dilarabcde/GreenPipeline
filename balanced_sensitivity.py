
import pandas as pd
from collections import Counter
from decision_engine import load_carbon_data, schedule_job

carbon_data = load_carbon_data()
jobs = pd.read_csv("data/jobs_fargate.csv")

tolerances = [0, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20]
records = []

for tolerance in tolerances:
    results = []
    regions = Counter()

    for _, job in jobs.iterrows():
        result = schedule_job(
            job,
            carbon_data,
            max_cost_usd=0.25,
            strategy="balanced",
            extra_cost_usd=tolerance
        )

        if result is not None:
            results.append(result)
            regions[result["region"]] += 1

    records.append({
        "tolerance_usd": tolerance,
        "planned": len(results),
        "total_cost_usd": sum(
            r["cost_usd"] for r in results
        ),
        "total_carbon_g": sum(
            r["carbon_g"] for r in results
        ),
        "frankfurt": regions["eu-central-1"],
        "stockholm": regions["eu-north-1"],
        "dublin": regions["eu-west-1"]
    })

df = pd.DataFrame(records)

baseline = df.iloc[0]

df["carbon_reduction_pct"] = (
    1 - df["total_carbon_g"] / baseline["total_carbon_g"]
) * 100

df["cost_increase_pct"] = (
    df["total_cost_usd"] / baseline["total_cost_usd"] - 1
) * 100

print("\nGREENPIPELINE BALANCED - DUYARLILIK ANALIZI")
print(df.round(4).to_string(index=False))

df.to_csv("data/balanced_sensitivity.csv", index=False)

print("\nSonuclar kaydedildi: data/balanced_sensitivity.csv")
