from flask import Blueprint, jsonify, request, current_app
from ..database import models as db

instellingen_bp = Blueprint("instellingen", __name__)


@instellingen_bp.get("/")
def get_all():
    return jsonify(db.get_all_instellingen(current_app.config["DB_PATH"]))


@instellingen_bp.put("/")
def update_all():
    data = request.get_json(force=True)
    db_path = current_app.config["DB_PATH"]
    for sleutel, waarde in data.items():
        db.set_instelling(db_path, sleutel, str(waarde))
    return jsonify({"ok": True})
