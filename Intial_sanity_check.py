# intial_sanity_check
from sqlalchemy import create_engine, text
from tabulate import tabulate

engine = create_engine("sqlite:///weather.db")

with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table';"
    )).fetchall()

print(tabulate(rows, headers=["Tables present"]))
