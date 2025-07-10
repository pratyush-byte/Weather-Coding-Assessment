"""
——— Quick start ——
    pip install Flask flask-restx sqlalchemy
    python app_flask.py   # runs on http://127.0.0.1:5000
"""
from __future__ import annotations

import math
from datetime import date, datetime
from typing import Optional

from flask import Flask, jsonify, request
from flask_restx import Api, Resource, fields
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session, sessionmaker

# ---------------------------------------------------------------------------
# Database (SQLite file created earlier)
# ---------------------------------------------------------------------------
engine = create_engine("sqlite:///weather.db", future=True)
SessionLocal = sessionmaker(bind=engine, future=True)

from model import DailyWeather, WeatherYearlyStats  # noqa: E402 (local file)

# ---------------------------------------------------------------------------
# Flask + flask‑restx setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
api = Api(app, version="1.0", title="Weather API", doc="/docs")

ns = api.namespace("api", description="Weather operations")

# Serialisation models (for Swagger)
weather_model = api.model(
    "DailyWeather",
    {
        "station_id": fields.String,
        "date": fields.String(example="1985-01-01"),
        "tmax_tc10": fields.Integer,
        "tmin_tc10": fields.Integer,
        "precip_tmm10": fields.Integer,
    },
)

yearly_model = api.model(
    "WeatherYearly",
    {
        "station_id": fields.String,
        "year": fields.Integer,
        "avg_tmax_c": fields.Float,
        "avg_tmin_c": fields.Float,
        "total_precip_cm": fields.Float,
    },
)

meta_model = api.model(
    "PageMeta",
    {
        "page": fields.Integer,
        "page_size": fields.Integer,
        "total_pages": fields.Integer,
        "total_items": fields.Integer,
    },
)

paginated_weather = api.model(
    "PaginatedWeather",
    {
        "meta": fields.Nested(meta_model),
        "data": fields.List(fields.Nested(weather_model)),
    },
)

paginated_yearly = api.model(
    "PaginatedYearly",
    {
        "meta": fields.Nested(meta_model),
        "data": fields.List(fields.Nested(yearly_model)),
    },
)

# ---------------------------------------------------------------------------
# Helper – pagination
# ---------------------------------------------------------------------------

def paginate(query, page: int, page_size: int, db: Session):
    total_items = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    total_pages = max(1, math.ceil(total_items / page_size))
    if page > total_pages:
        return None, []

    rows = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    meta = {
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_items": total_items,
    }
    return meta, rows

# ---------------------------------------------------------------------------
# /api/weather  --------------------------------------------------------------
# ---------------------------------------------------------------------------
@ns.route("/weather")
class WeatherDailyAPI(Resource):
    @ns.doc(params={
        "station_id": "Station code",
        "date": "Exact date (YYYY-MM-DD)",
        "start": "Start date (inclusive)",
        "end": "End date (inclusive)",
        "page": "Page number (default 1)",
        "page_size": "Rows per page (1‑500, default 50)",
    })
    @ns.marshal_with(paginated_weather)
    def get(self):
        db: Session = SessionLocal()
        try:
            station_id: Optional[str] = request.args.get("station_id")
            date_str = request.args.get("date")
            start_str = request.args.get("start")
            end_str = request.args.get("end")
            page = int(request.args.get("page", 1))
            page_size = min(max(int(request.args.get("page_size", 50)), 1), 500)

            qry = select(DailyWeather)
            if station_id:
                qry = qry.where(DailyWeather.station_id == station_id)
            if date_str:
                qry = qry.where(DailyWeather.date == date.fromisoformat(date_str))
            if start_str:
                qry = qry.where(DailyWeather.date >= date.fromisoformat(start_str))
            if end_str:
                qry = qry.where(DailyWeather.date <= date.fromisoformat(end_str))

            meta, rows = paginate(qry, page, page_size, db)
            if meta is None:
                api.abort(404, "Page out of range")
            return {"meta": meta, "data": rows}
        finally:
            db.close()

# ---------------------------------------------------------------------------
# /api/weather/stats  --------------------------------------------------------
# ---------------------------------------------------------------------------
@ns.route("/weather/stats")
class WeatherYearlyAPI(Resource):
    @ns.doc(params={
        "station_id": "Station code",
        "year": "Four‑digit year",
        "page": "Page number (default 1)",
        "page_size": "Rows per page (1‑500, default 50)",
    })
    @ns.marshal_with(paginated_yearly)
    def get(self):
        db: Session = SessionLocal()
        try:
            station_id: Optional[str] = request.args.get("station_id")
            year_str = request.args.get("year")
            page = int(request.args.get("page", 1))
            page_size = min(max(int(request.args.get("page_size", 50)), 1), 500)

            qry = select(WeatherYearlyStats)
            if station_id:
                qry = qry.where(WeatherYearlyStats.station_id == station_id)
            if year_str:
                qry = qry.where(WeatherYearlyStats.year == int(year_str))

            meta, rows = paginate(qry, page, page_size, db)
            if meta is None:
                api.abort(404, "Page out of range")
            return {"meta": meta, "data": rows}
        finally:
            db.close()

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@ns.route("/Check")
class Ping(Resource):
    def get(self):
        return {"message": "Server is running!"}, 200

# ---------------------------------------------------------------------------
# Entry‑point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Debug server – accessible at http://127.0.0.1:5000
    from werkzeug.middleware.proxy_fix import ProxyFix

    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(debug=True)
