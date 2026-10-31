
import pandas as pd

from decision_engine import load_carbon_data, schedule_job

# Deneyeceğimiz görev başına bütçe sınırları ($)
BUDGETS = [0.01, 0.05, 0.10, 0.25, 0.50, 2.00]

jobs = pd.read_csv("data/jobs_stress_fargate.csv")
carbon_data = load_carbon_data()

results = []

for budget in BUDGETS:
    completed = 0
    total_cost = 0.0
    total_carbon = 0.0
    frankfurt = 0
    stockholm = 0

    for _, job in jobs.iterrows():
        decision = schedule_job(
            job,
            carbon_data,
            max_cost_usd=budget
        )

        if decision is None:
            # Bu görev bütçe/deadline koşullarını
            # sağlayan bir seçeneğe sahip değil.
            continue

        completed += 1
        total_cost += decision["cost_usd"]
        total_carbon += decision["carbon_g"]

        if decision["region"] == "eu-central-1":
            frankfurt += 1
        elif decision["region"] == "eu-north-1":
            stockholm += 1

    results.append({
        "budget_usd": budget,
        "total_jobs": len(jobs),
        "completed": completed,
        "unassigned": len(jobs) - completed,
        "completion_rate_pct": 100 * completed / len(jobs),
        "total_cost_usd": round(total_cost, 4),
        "total_carbon_g": round(total_carbon, 4),
        "frankfurt": frankfurt,
        "stockholm": stockholm
    })

df = pd.DataFrame(results)

print("\nGREENPIPELINE - BÜTÇE ANALİZİ")
print(df.to_string(index=False))

print("\nUYARI:")
print("Eksik görev bulunan senaryolarda toplam karbon")
print("ve maliyet değerleri doğrudan karşılaştırılamaz.")
print("Çünkü her bütçede aynı sayıda görev tamamlanmamış olabilir.")

df.to_csv("data/budget_results.csv", index=False)

print("\nSonuçlar data/budget_results.csv dosyasına kaydedildi.")
