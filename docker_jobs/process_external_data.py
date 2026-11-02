
import csv
import time
from pathlib import Path

INPUT_FILE = Path("/input/owid_energy.csv")

start = time.perf_counter()

countries = set()
years = set()
total_rows = 0
missing_country = 0

with INPUT_FILE.open(
    "r", encoding="utf-8-sig", newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:
        total_rows += 1

        country = row.get("country", "").strip()
        year = row.get("year", "").strip()

        if country:
            countries.add(country)
        else:
            missing_country += 1

        if year:
            years.add(year)

elapsed = time.perf_counter() - start

print("GERÇEK VERİ İŞLEME SONUCU")
print("Toplam kayıt:", total_rows)
print("Ülke/bölge sayısı:", len(countries))
print("Farklı yıl sayısı:", len(years))
print("Ülkesi eksik kayıt:", missing_country)
print("Dosya boyutu (MB):",
      round(INPUT_FILE.stat().st_size / 1_000_000, 3))
print("İşlem süresi (sn):", round(elapsed, 4))
print("Görev başarıyla tamamlandı.")
