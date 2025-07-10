from __future__ import annotations

import logging
from datetime import datetime as dt
from pathlib import Path
from typing import List, Tuple

from sqlalchemy import create_engine
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from model import Base, Station, DailyWeather

# ────────────────────────────────────────────────────────────────────────────────
# Paths / constants
# ────────────────────────────────────────────────────────────────────────────────
DB_URL  = "sqlite:///weather.db"          # change to Postgres URL if desired
WX_DIR  = Path("wx_data")                 # raw files folder
LOG_DIR = Path("logs"); LOG_DIR.mkdir(exist_ok=True)

BATCH_SIZE_SQLITE   = 180     # 180 × 5 params = 900 < 999
BATCH_SIZE_POSTGRES = 10_000

# ────────────────────────────────────────────────────────────────────────────────
# Logging
# ────────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "ingest.log", mode="a", encoding="utf-8"),
    ],
)

# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────

def _nullify(raw: str) -> int | None:
    val = int(raw)
    return None if val == -9999 else val


def _parse_line(line: str):
    date_str, tmax, tmin, precip = line.rstrip().split("\t")
    return {
        "date": dt.strptime(date_str, "%Y%m%d").date(),
        "tmax_tc10": _nullify(tmax),
        "tmin_tc10": _nullify(tmin),
        "precip_tmm10": _nullify(precip),
    }

# ────────────────────────────────────────────────────────────────────────────────
# Ingest
# ────────────────────────────────────────────────────────────────────────────────

def ingest() -> None:
    start = dt.now()
    total_new = total_dup = 0

    engine = create_engine(DB_URL, future=True)
    Base.metadata.create_all(engine)
    is_sqlite = engine.url.get_backend_name() == "sqlite"
    batch_size = BATCH_SIZE_SQLITE if is_sqlite else BATCH_SIZE_POSTGRES

    with Session(engine) as session:
        for filepath in sorted(WX_DIR.glob("US*.txt")):
            station_id = filepath.stem
            logging.info("Processing %-12s …", station_id)

            # Upsert station row
            stmt_station = (
                (sqlite_insert if is_sqlite else pg_insert)(Station)
                .values(id=station_id)
                .on_conflict_do_nothing()
            )
            session.execute(stmt_station)

            buf: List[dict[str, object]] = []
            file_new = file_dup = 0

            with filepath.open() as fh:
                for line in fh:
                    buf.append({"station_id": station_id, **_parse_line(line)})
                    if len(buf) == batch_size:
                        n_new, n_dup = _flush(buf, session, is_sqlite)
                        file_new += n_new; file_dup += n_dup

            if buf:
                n_new, n_dup = _flush(buf, session, is_sqlite)
                file_new += n_new; file_dup += n_dup

            session.commit()  # commit per file
            total_new += file_new; total_dup += file_dup
            logging.info("  ↳ %s new · %s dup", f"{file_new:,}", f"{file_dup:,}")

    secs = (dt.now() - start).total_seconds()
    logging.info(
        "Done: %s new · %s dup · %.1f s elapsed",
        f"{total_new:,}", f"{total_dup:,}", secs,
    )

# ────────────────────────────────────────────────────────────────────────────────
# Flush helper
# ────────────────────────────────────────────────────────────────────────────────

def _flush(buf: list[dict[str, object]], session: Session, is_sqlite: bool) -> Tuple[int, int]:
    if not buf:
        return 0, 0

    stmt = (
        (sqlite_insert if is_sqlite else pg_insert)(DailyWeather)
        .values(buf)
        .on_conflict_do_nothing(index_elements=["station_id", "date"])
    )
    result: Result = session.execute(stmt)

    inserted = result.rowcount or 0       # rowcount excludes skipped rows
    duplicates = len(buf) - inserted
    buf.clear()
    return inserted, duplicates


if __name__ == "__main__":
    try:
        ingest()
    except KeyboardInterrupt:
        logging.warning("Interrupted by user – partial commits saved.")
