from flask import Blueprint

from app.health.api import health_blueprint

api_v1 = Blueprint("api_v1", __name__)
api_v1.register_blueprint(health_blueprint)
