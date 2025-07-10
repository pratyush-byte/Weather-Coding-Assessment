from flask_restx import Resource
from flask import request
from sqlalchemy import select
from model import DailyWeather, WeatherYearlyStats
from api.pagination import paginate, get_pagination_params

def register_routes(api, ns, SessionLocal, models):
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
        @ns.marshal_with(models["paginated_weather"])
        def get(self):
            db = SessionLocal()
            try:
                station_id = request.args.get("station_id")
                date_str = request.args.get("date")
                start_str = request.args.get("start")
                end_str = request.args.get("end")
                page, page_size = get_pagination_params(api)
                qry = select(DailyWeather)
                if station_id:
                    qry = qry.where(DailyWeather.station_id == station_id)
                if date_str:
                    qry = qry.where(DailyWeather.date == date_str)
                if start_str:
                    qry = qry.where(DailyWeather.date >= start_str)
                if end_str:
                    qry = qry.where(DailyWeather.date <= end_str)
                meta, rows = paginate(qry, page, page_size, db)
                if meta is None:
                    api.abort(404, "Page out of range")
                return {"meta": meta, "data": rows}
            finally:
                db.close()

    @ns.route("/weather/stats")
    class WeatherYearlyAPI(Resource):
        @ns.doc(params={
            "station_id": "Station code",
            "year": "Four‑digit year",
            "page": "Page number (default 1)",
            "page_size": "Rows per page (1‑500, default 50)",
        })
        @ns.marshal_with(models["paginated_yearly"])
        def get(self):
            db = SessionLocal()
            try:
                station_id = request.args.get("station_id")
                year_str = request.args.get("year")
                page, page_size = get_pagination_params(api)
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