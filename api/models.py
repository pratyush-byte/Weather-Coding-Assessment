from flask_restx import fields

def register_models(api):
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
    return {
        "weather_model": weather_model,
        "yearly_model": yearly_model,
        "meta_model": meta_model,
        "paginated_weather": paginated_weather,
        "paginated_yearly": paginated_yearly,
    }