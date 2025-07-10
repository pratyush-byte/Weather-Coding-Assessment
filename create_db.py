#Run this one time to create a SQLite database with the necessary tables.
from sqlalchemy import create_engine
from model import Base

engine = create_engine("sqlite:///weather.db")  # local file weather.db
Base.metadata.create_all(engine)

print("Tables created!  (Open weather.db with DB Browser for SQLite if curious.)")