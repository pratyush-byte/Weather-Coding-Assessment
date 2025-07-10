"""Quick sanity checker for the SQLite DB.

Shows:
  • total raw‑daily rows
  • station count
  • yearly‑stats row count
  • first N samples from each table (tabulated)

Run:
    python check_counts.py
"""
from __future__ import annotations

from sqlalchemy import create_engine, text
from tabulate import tabulate

engine = create_engine("sqlite:///weather.db", future=True)

SAMPLE_N = 10  # number of rows to preview from each table

with engine.connect() as conn:
    # ------- counts -----------------------------------------------------
    total_daily   = conn.scalar(text("SELECT COUNT(*) FROM weather_daily"))
    station_cnt   = conn.scalar(text("SELECT COUNT(*) FROM station"))
    yearly_cnt    = conn.scalar(text("SELECT COUNT(*) FROM weather_yearly_stats"))

    # ------- samples ----------------------------------------------------
    daily_sample = conn.execute(text(
        "SELECT station_id, date, tmax_tc10, tmin_tc10, precip_tmm10 "
        f"FROM weather_daily LIMIT {SAMPLE_N}"))

    yearly_sample = conn.execute(text(
        "SELECT station_id, year, avg_tmax_c, avg_tmin_c, total_precip_cm "
        f"FROM weather_yearly_stats LIMIT {SAMPLE_N}"))

print("\n=== Row Counts ===")
print(f"Raw daily rows   : {total_daily:,}")
print(f"Stations         : {station_cnt}")
print(f"Yearly stats rows: {yearly_cnt:,}")

print("\n=== Daily table – first" , SAMPLE_N, "rows ===")
print(tabulate(daily_sample, headers=["station", "date", "tmax", "tmin", "precip"], tablefmt="github"))

print("\n=== Yearly table – first", SAMPLE_N, "rows ===")
print(tabulate(yearly_sample, headers=["station", "year", "avg_tmax", "avg_tmin", "precip_cm"], tablefmt="github"))
