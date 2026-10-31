
import pandas as pd

CARBON_COLUMN = "Carbon intensity gCO₂eq/kWh (Life cycle)"
TIME_COLUMN = "Datetime (UTC)"

files = {
    "Frankfurt": "data/raw/snapshots_2026-02-10_DE-2025-hourly.csv",
    "Stockholm": "data/raw/snapshots_2026-02-10_SE-SE3-2025-hourly.csv"
}

# Gerçek karbon verilerini yükle
carbon_data = {}

for region, path in files.items():
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df[TIME_COLUMN], utc=True)

    df = df.set_index("time").sort_index()
    carbon_data[region] = df

    print(f"{region}: {len(df)} saatlik kayıt")

# Stress test görevlerinden ilkini seç
jobs = pd.read_csv("data/jobs_stress.csv")
job = jobs.iloc[0]

arrival = pd.to_datetime(job["arrival_time"], utc=True)
hour = arrival.floor("h")

print("\nİLK GÖREV")
print("Görev ID:", job["job_id"])
print("Geliş zamanı:", arrival)
print("Veri boyutu:", job["data_size_gb"], "GB")
print("Çalışma süresi:", job["duration_min"], "dakika")

print("\nGERÇEK KARBON YOĞUNLUĞU")

for region, df in carbon_data.items():
    intensity = df.loc[hour, CARBON_COLUMN]
    print(f"{region}: {intensity:.2f} gCO2eq/kWh")
