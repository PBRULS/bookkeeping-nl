from flask import Blueprint, jsonify, current_app, request
from datetime import datetime
from ..database import models as db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
def get_dashboard():
    jaar = request.args.get("jaar", datetime.now().year, type=int)
    stats = db.get_dashboard_stats(current_app.config["DB_PATH"], jaar)
    return jsonify(stats)
