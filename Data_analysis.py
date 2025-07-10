import logging
import time
from db import get_connection, fetch_all_stats, run_agg_query
from stats import Stats, fmt

AGG_QUERY = """
INSERT INTO weather_yearly_stats (
    station_id, year, avg_tmax_c, avg_tmin_c, total_precip_cm)
SELECT
    station_id,
    CAST(strftime('%Y', date) AS INTEGER)          AS yr,
    ROUND(AVG(tmax_tc10)  / 10.0, 1)              AS avg_tmax_c,
    ROUND(AVG(tmin_tc10)  / 10.0, 1)              AS avg_tmin_c,
    ROUND(SUM(precip_tmm10) / 100.0, 1)           AS total_precip_cm
FROM weather_daily
GROUP BY station_id, yr;
"""

def main():
    """
    Run yearly aggregation of weather data and log before/after stats.
    """
    # Configure logging to write to data_analysis.log with timestamps and levels
    logging.basicConfig(
        filename='logs/data_analysis.log',
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    log = logging.getLogger(__name__)
    log.info("▶︎ Yearly aggregation started (SQLite)")
    start = time.perf_counter()

    with get_connection() as conn:
        # Fetch stats before aggregation
        before = { (sid, yr): Stats(tmax, tmin, precip)
                   for sid, yr, tmax, tmin, precip in fetch_all_stats(conn) }
        log.info("Existing station‑year rows: %s", f"{len(before):,}")

        # Run aggregation query
        run_agg_query(conn, AGG_QUERY)

        # Fetch stats after aggregation
        after = { (sid, yr): Stats(tmax, tmin, precip)
                  for sid, yr, tmax, tmin, precip in fetch_all_stats(conn) }

        # Example: Log new rows (diff logic can be improved as needed)
        new_rows = set(after.keys()) - set(before.keys())
        for sid, yr in sorted(new_rows):
            stats = after[(sid, yr)]
            log.info(
                "NEW   %s %s  Tmax=%s  Tmin=%s  Precip=%s",
                sid, yr, fmt(stats.tmax), fmt(stats.tmin), fmt(stats.precip)
            )

    elapsed = time.perf_counter() - start
    log.info("Yearly aggregation finished in %.2f seconds", elapsed)

if __name__ == "__main__":
    main()