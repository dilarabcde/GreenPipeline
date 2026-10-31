
import pandas as pd

# İlk simülasyon için örnek fiyatlar ($/saat)
# Bunlar doğrulanmış güncel AWS fiyatları değildir.
PRICES = {
    "eu-central-1": {
        "name": "Frankfurt",
        "vcpu_hour": 0.04656,
        "memory_gb_hour": 0.00511
    },
    "eu-north-1": {
        "name": "Stockholm",
        "vcpu_hour": 0.04450,
        "memory_gb_hour": 0.00490
    }
}

# Varsayımsal bölgeler arası transfer ücreti
TRANSFER_PRICE_PER_GB = 0.02


def calculate_compute_cost(job, region):
    # Fargate minimum faturalandırma süresi: 1 dakika
    hours = max(float(job["duration_min"]), 1) / 60

    cpu = float(job["cpu"])
    memory = float(job["memory_gb"])

    price = PRICES[region]

    return hours * (
        cpu * price["vcpu_hour"]
        + memory * price["memory_gb_hour"]
    )


def calculate_transfer_cost(job, target_region):
    source_region = job["data_region"]

    # Veri zaten hedef bölgedeyse transfer yok
    if source_region == target_region:
        return 0.0

    return (
        float(job["data_size_gb"])
        * TRANSFER_PRICE_PER_GB
    )


def calculate_total_cost(job, target_region):
    compute = calculate_compute_cost(job, target_region)
    transfer = calculate_transfer_cost(job, target_region)

    return compute, transfer, compute + transfer


jobs = pd.read_csv("data/jobs_stress.csv")
job = jobs.iloc[0]

print("GÖREV:", job["job_id"])
print("Verinin bulunduğu bölge:", job["data_region"])
print("Veri boyutu:", job["data_size_gb"], "GB")

for region, info in PRICES.items():
    compute, transfer, total = calculate_total_cost(
        job, region
    )

    print(f"\n{info['name']}")
    print(f"İşlem maliyeti: ${compute:.4f}")
    print(f"Aktarım maliyeti: ${transfer:.4f}")
    print(f"Toplam maliyet: ${total:.4f}")
