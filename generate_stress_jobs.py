
import pandas as pd
import random

random.seed(42)

# Mevcut görevleri oku
jobs = pd.read_csv("data/jobs.csv")

# Üç farklı deadline senaryosu
slack_ranges = {
    "urgent": (5, 20),
    "normal": (30, 90),
    "flexible": (120, 360)
}

for i in range(len(jobs)):
    # Görevleri üç gruba ayır
    category = ["urgent", "normal", "flexible"][i % 3]

    min_slack, max_slack = slack_ranges[category]
    slack = random.randint(min_slack, max_slack)

    arrival = pd.to_datetime(jobs.loc[i, "arrival_time"])
    duration = jobs.loc[i, "duration_min"]

    jobs.loc[i, "deadline"] = (
        arrival + pd.Timedelta(minutes=duration + slack)
    ).isoformat()

    jobs.loc[i, "priority"] = category

# Eski dosyaya dokunmadan yeni dosyaya kaydet
jobs.to_csv("data/jobs_stress.csv", index=False)

print("Stress test veri seti oluşturuldu!")
print(jobs["priority"].value_counts())
