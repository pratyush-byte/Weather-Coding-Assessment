from __future__ import annotations

import logging
import time
from collections import namedtuple
from pathlib import Path
from typing import Dict, Tuple, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Result

# ---------------------------------------------------------------------------
# Logging – dedicated file for Problem‑3 analysis
# ---------------------------------------------------------------------------
LOG_FILE = Path(__file__).with_suffix("").parent / "logs" / "data_analysis.log"
LOG_FILE.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(),  # also echo to console
    ],
    force=True,  # override if another script already set up logging
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database – fixed to SQLite
# ---------------------------------------------------------------------------
engine = create_engine("sqlite:///weather.db", future=True)

# Single aggregate query (SQLite dialect)
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

# Named‑tuple for diff readability
Stats = namedtuple("Stats", "tmax tmin precip")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(x: Optional[float]) -> str:
    """Format numbers nicely; return 'NA' if value is None."""
    return "NA" if x is None else f"{x:.1f}"


def _fetch_all_stats(conn: Connection) -> Dict[Tuple[str, int], Stats]:
    """Dump the current yearly stats into a dict."""
    rows: Result = conn.execute(text(
        "SELECT station_id, year, avg_tmax_c, avg_tmin_c, total_precip_cm "
        "FROM weather_yearly_stats"))
    return {(sid, yr): Stats(tmax, tmin, precip) for sid, yr, tmax, tmin, precip in rows}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("▶︎ Yearly aggregation started (SQLite)")
    start = time.perf_counter()

    with engine.begin() as conn:
        before = _fetch_all_stats(conn)
        log.info("Existing station‑year rows: %s", f"{len(before):,}")

        conn.execute(text("DELETE FROM weather_yearly_stats"))
        conn.execute(text(AGG_QUERY))

        after = _fetch_all_stats(conn)

    # diff
    added = changed = same = 0
    for key, new in after.items():
        old = before.get(key)
        if old is None:
            added += 1
            log.info(
                "NEW   %s %4d  Tmax=%s  Tmin=%s  Precip=%s",
                key[0], key[1], _fmt(new.tmax), _fmt(new.tmin), _fmt(new.precip)
            )
        elif old != new:
            changed += 1
            log.info(
                "CHG   %s %4d  %s→%s  %s→%s  %s→%s",
                key[0], key[1],
                _fmt(old.tmax), _fmt(new.tmax),
                _fmt(old.tmin), _fmt(new.tmin),
                _fmt(old.precip), _fmt(new.precip)
            )
        else:
            same += 1

    removed = len(before) - (added + changed + same)
    elapsed = time.perf_counter() - start
    log.info(
        "Yearly aggregation finished: %s added · %s changed · %s removed · %s unchanged (%.2f s)",
        f"{added:,}", f"{changed:,}", f"{removed:,}", f"{same:,}", elapsed
    )


if __name__ == "__main__":
    main()
