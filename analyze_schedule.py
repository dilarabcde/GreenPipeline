
import pandas as pd
from database import connect

db = connect()

try:
    df = pd.read_sql_query("""
        SELECT
            run_id,
            job_id,
            status,
            scheduled_at,
            started_at,
            finished_at,
            actual_runtime_seconds
        FROM job_runs
        WHERE scheduled_at IS NOT NULL
        ORDER BY run_id
    """, db)
finally:
    db.close()

if df.empty:
    print("Henüz planlanmış görev bulunamadı.")
else:
    for column in ["scheduled_at", "started_at", "finished_at"]:
        df[column] = pd.to_datetime(df[column], utc=True)

    df["start_delay_seconds"] = (
        df["started_at"] - df["scheduled_at"]
    ).dt.total_seconds()

    print("\nGREENPIPELINE ZAMANLAMA ANALİZİ")
    print(df[[
        "run_id",
        "status",
        "start_delay_seconds",
        "actual_runtime_seconds"
    ]].to_string(index=False))

    completed = df[df["status"] == "Completed"]

    if not completed.empty:
        print(
            "\nOrtalama başlatma gecikmesi:",
            round(completed["start_delay_seconds"].mean(), 4),
            "saniye"
        )
