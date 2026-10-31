
import pandas as pd

# AWS Fargate Linux için geçerli CPU/RAM kombinasyonları
VALID_CONFIGS = {
    0.25: [0.5, 1.0, 2.0],
    0.5: [1.0, 2.0, 3.0, 4.0],
    1.0: [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
}


def fix_resources(row):
    cpu = float(row["cpu"])
    memory = float(row["memory_gb"])

    allowed = VALID_CONFIGS[cpu]

    # İstenen RAM'i karşılayan en küçük geçerli değer
    new_memory = next(
        m for m in allowed if m >= memory
    )

    row["memory_gb"] = new_memory
    return row


for name in ["jobs", "jobs_stress"]:
    original = pd.read_csv(f"data/{name}.csv")

    corrected = original.apply(
        fix_resources, axis=1
    )

    changed = (
        original["memory_gb"]
        != corrected["memory_gb"]
    ).sum()

    output = f"data/{name}_fargate.csv"
    corrected.to_csv(output, index=False)

    print(f"\n{name}")
    print(f"Toplam görev: {len(corrected)}")
    print(f"RAM değeri düzeltilen: {changed}")
    print(f"Kaydedildi: {output}")
