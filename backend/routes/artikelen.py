from flask import Blueprint, jsonify, request, current_app
from ..database import models as db

artikelen_bp = Blueprint("artikelen", __name__)


@artikelen_bp.get("/")
def lijst():
    items = db.get_artikelen(current_app.config["DB_PATH"])
    # Enrich with current stock level
    for item in items:
        if item.get("voorraad_bijhouden"):
            item["voorraad_stand"] = db.get_voorraad_stand(
                current_app.config["DB_PATH"], item["id"]
            )
    return jsonify(items)


@artikelen_bp.get("/<int:aid>")
def detail(aid):
    item = db.get_artikel(current_app.config["DB_PATH"], aid)
    if item is None:
        return jsonify({"error": "Niet gevonden"}), 404
    if item.get("voorraad_bijhouden"):
        item["voorraad_stand"] = db.get_voorraad_stand(
            current_app.config["DB_PATH"], aid
        )
    return jsonify(item)


@artikelen_bp.post("/")
def aanmaken():
    data = request.get_json(force=True)
    if not data.get("naam"):
        return jsonify({"error": "Veld 'naam' is verplicht"}), 400
    aid = db.create_artikel(current_app.config["DB_PATH"], data)
    return jsonify({"id": aid}), 201


@artikelen_bp.put("/<int:aid>")
def bijwerken(aid):
    data = request.get_json(force=True)
    db.update_artikel(current_app.config["DB_PATH"], aid, data)
    return jsonify({"ok": True})
