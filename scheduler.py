
import pandas as pd

# Görev verilerimizi oku
jobs = pd.read_csv("data/jobs_stress.csv")

# Örnek ağ hızı: 100 Mbps
# Bu değer simülasyon varsayımıdır.
TRANSFER_SPEED_MBPS = 100


def calculate_transfer_time(data_size_gb):
    # GB -> gigabit -> saniye -> dakika
    transfer_minutes = (
        data_size_gb * 8 * 1000
    ) / (TRANSFER_SPEED_MBPS * 60)

    return transfer_minutes


def check_deadline(job):
    arrival = pd.to_datetime(job["arrival_time"])
    deadline = pd.to_datetime(job["deadline"])

    duration = job["duration_min"]
    data_size = job["data_size_gb"]

    transfer_time = calculate_transfer_time(data_size)

    # Frankfurt: veri zaten burada
    frankfurt_finish = arrival + pd.Timedelta(
        minutes=duration
    )

    # Stockholm: önce veri aktarılıyor
    stockholm_finish = arrival + pd.Timedelta(
        minutes=transfer_time + duration
    )

    return {
        "job_id": job["job_id"],
        "data_size_gb": data_size,
        "transfer_min": round(transfer_time, 2),
        "frankfurt_feasible": frankfurt_finish <= deadline,
        "stockholm_feasible": stockholm_finish <= deadline
    }


results = []

for _, job in jobs.iterrows():
    results.append(check_deadline(job))

df_results = pd.DataFrame(results)

print(df_results.head(10).to_string(index=False))

print("\nFrankfurt'ta yetişen görev:",
      df_results["frankfurt_feasible"].sum())

print("Stockholm'de yetişen görev:",
      df_results["stockholm_feasible"].sum())
