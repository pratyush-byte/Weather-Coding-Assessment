from sqlalchemy import (
    Column, Integer, Float, String, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ------------------------------------------------------------------
# Station
# ------------------------------------------------------------------
class Station(Base):
    __tablename__ = "station"

    id   = Column(String(11), primary_key=True)
    name = Column(String, nullable=True)

    # existing “daily” one-to-many
    daily = relationship(
        "DailyWeather",
        back_populates="station",
        cascade="all, delete-orphan",
    )

    # ✧ NEW ✧ add the missing collection for yearly stats
    yearly = relationship(
        "WeatherYearlyStats",
        back_populates="station",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

# ------------------------------------------------------------------
# Daily observations (unchanged)
# ------------------------------------------------------------------
class DailyWeather(Base):
    __tablename__ = "weather_daily"
    station_id = Column(String(11), ForeignKey("station.id"), primary_key=True)
    date       = Column(String, primary_key=True)          # YYYY-MM-DD text
    tmax_tc10  = Column(Integer)                           # raw tenths °C
    tmin_tc10  = Column(Integer)
    precip_tmm10 = Column(Integer)                         # raw tenths mm

    station = relationship("Station", back_populates="daily")

# ------------------------------------------------------------------
# Yearly aggregates  (Problem 3)
# ------------------------------------------------------------------
class WeatherYearlyStats(Base):
    __tablename__ = "weather_yearly_stats"

    station_id = Column(
        String(11),
        ForeignKey("station.id", ondelete="CASCADE"),
        primary_key=True,
    )
    year = Column(Integer, primary_key=True)

    avg_tmax_c      = Column(Float)   # °C
    avg_tmin_c      = Column(Float)   # °C
    total_precip_cm = Column(Float)   # cm

    # **make sure the string matches Station.yearly**
    station = relationship("Station", back_populates="yearly")
