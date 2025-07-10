from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Result

engine = create_engine("sqlite:///weather.db", future=True)

def get_connection():
    return engine.begin()

def fetch_all_stats(conn: Connection):
    rows: Result = conn.execute(text(
        "SELECT station_id, year, avg_tmax_c, avg_tmin_c, total_precip_cm "
        "FROM weather_yearly_stats"))
    return list(rows)

def run_agg_query(conn: Connection, agg_query: str):
    conn.execute(text("DELETE FROM weather_yearly_stats"))
    conn.execute(text(agg_query))