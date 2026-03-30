from flask import Blueprint, jsonify, request, current_app
from ..database import models as db

relaties_bp = Blueprint("relaties", __name__)


@relaties_bp.get("/")
def lijst():
    type_filter = request.args.get("type")
    return jsonify(db.get_relaties(current_app.config["DB_PATH"], type_filter))


@relaties_bp.get("/<int:rid>")
def detail(rid):
    item = db.get_relatie(current_app.config["DB_PATH"], rid)
    if item is None:
        return jsonify({"error": "Niet gevonden"}), 404
    return jsonify(item)


@relaties_bp.post("/")
def aanmaken():
    data = request.get_json(force=True)
    required = ["type", "naam"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Veld '{field}' is verplicht"}), 400
    rid = db.create_relatie(current_app.config["DB_PATH"], data)
    return jsonify({"id": rid}), 201


@relaties_bp.put("/<int:rid>")
def bijwerken(rid):
    data = request.get_json(force=True)
    db.update_relatie(current_app.config["DB_PATH"], rid, data)
    return jsonify({"ok": True})
