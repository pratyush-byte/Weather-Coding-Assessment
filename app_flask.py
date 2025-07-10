
from flask import Flask
from flask_restx import Api

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.models import register_models
from api.routes import register_routes

engine = create_engine("sqlite:///weather.db", future=True)
SessionLocal = sessionmaker(bind=engine, future=True)

app = Flask(__name__)
api = Api(app, version="1.0", title="Weather API", doc="/docs")
ns = api.namespace("api", description="Weather operations")

models = register_models(api)
register_routes(api, ns, SessionLocal, models)

if __name__ == "__main__":
    app.run(debug=True)

