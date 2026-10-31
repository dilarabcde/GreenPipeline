
import csv
import hashlib
import time
from pathlib import Path

start = time.perf_counter()

# 50.000 veri kaydı üret ve işle
output = Path("/tmp/processed_data.csv")

with output.open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["id", "hash"])

    for i in range(5_000_000):
        value = hashlib.sha256(
            f"greenpipeline-{i}".encode()
        ).hexdigest()

        writer.writerow([i, value])

elapsed = time.perf_counter() - start

print("İşlenen kayıt sayısı: 50000")
print(f"Çalışma süresi: {elapsed:.4f} saniye")
print("Görev başarıyla tamamlandı.")
