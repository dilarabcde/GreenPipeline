
import pandas as pd

from cost_model import calculate_total_cost, PRICES

# Simülasyon parametreleri
TRANSFER_SPEED_MBPS = 100
MAX_COST_USD = 0.25

# Varsayımsal enerji tüketimi: kW / vCPU
POWER_KW_PER_VCPU = 0.10

CARBON_COLUMN = "Carbon intensity gCO₂eq/kWh (Life cycle)"

CARBON_FILES = {
    "eu-central-1": "data/raw/snapshots_2026-02-10_DE-2025-hourly.csv",
    "eu-north-1": "data/raw/snapshots_2026-02-10_SE-SE3-2025-hourly.csv",
    "eu-west-1": "data/raw/snapshots_2026-02-10_IE-2025-hourly.csv"
}


def load_carbon_data():
    result = {}

    for region, path in CARBON_FILES.items():
        df = pd.read_csv(path)
        df["time"] = pd.to_datetime(
            df["Datetime (UTC)"], utc=True
        )
        result[region] = df.set_index("time").sort_index()

    return result


def transfer_minutes(job, region):
    if job["data_region"] == region:
        return 0.0

    return (
        float(job["data_size_gb"]) * 8000
        / (TRANSFER_SPEED_MBPS * 60)
    )


def estimate_emissions(job, region, start, carbon_data):
    """Çalışma süresi boyunca tahmini karbon emisyonu."""
    end = start + pd.Timedelta(
        minutes=float(job["duration_min"])
    )

    power_kw = float(job["cpu"]) * POWER_KW_PER_VCPU
    total_grams = 0.0
    current = start

    while current < end:
        hour = current.floor("h")
        next_hour = hour + pd.Timedelta(hours=1)
        segment_end = min(end, next_hour)

        intensity = carbon_data[region].loc[
            hour, CARBON_COLUMN
        ]

        hours = (segment_end - current).total_seconds() / 3600
        total_grams += power_kw * hours * intensity

        current = segment_end

    return total_grams


def schedule_job(job, carbon_data, max_cost_usd=MAX_COST_USD):
    arrival = pd.to_datetime(job["arrival_time"], utc=True)
    deadline = pd.to_datetime(job["deadline"], utc=True)

    duration = pd.Timedelta(
        minutes=float(job["duration_min"])
    )

    candidates = []

    for region in PRICES:
        transfer = transfer_minutes(job, region)

        earliest = arrival + pd.Timedelta(minutes=transfer)
        latest = deadline - duration

        if earliest > latest:
            continue

        compute, transfer_cost, total_cost = (
            calculate_total_cost(job, region)
        )

        if total_cost > max_cost_usd:
            continue

        # Hemen başlayabilme + uygun saat başları
        starts = [earliest]
        next_hour = earliest.ceil("h")

        while next_hour <= latest:
            if next_hour not in starts:
                starts.append(next_hour)
            next_hour += pd.Timedelta(hours=1)

        for start in starts:
            try:
                emissions = estimate_emissions(
                    job, region, start, carbon_data
                )
            except KeyError:
                continue

            candidates.append({
                "region": region,
                "start": start,
                "finish": start + duration,
                "cost_usd": total_cost,
                "carbon_g": emissions,
                "transfer_min": transfer
            })

    if not candidates:
        return None

    # Önce minimum karbon, eşitlikte minimum maliyet
    return min(
        candidates,
        key=lambda x: (x["carbon_g"], x["cost_usd"])
    )


carbon_data = load_carbon_data()


if __name__ == "__main__":
    jobs = pd.read_csv("data/jobs_stress.csv")

    results = []

    for _, job in jobs.iterrows():
        decision = schedule_job(job, carbon_data)

        if decision is None:
            results.append({
                "job_id": job["job_id"],
                "region": "Uygun seçenek yok"
            })
        else:
            results.append({
                "job_id": job["job_id"],
                **decision
            })

    df = pd.DataFrame(results)

    print("\nGREENPIPELINE KARARLARI")
    print(df.head(10).to_string(index=False))

    print("\nBÖLGE SEÇİMLERİ")
    print(df["region"].value_counts())

    df.to_csv("data/decisions.csv", index=False)

    print("\nSonuçlar data/decisions.csv dosyasına kaydedildi.")
