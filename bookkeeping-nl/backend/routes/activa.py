from flask import Blueprint, jsonify, request, current_app
from ..database import models as db
from ..services import asset_service

activa_bp = Blueprint("activa", __name__)


@activa_bp.get("/")
def lijst():
    items = db.get_activa(current_app.config["DB_PATH"])
    for item in items:
        item["boekwaarde"] = asset_service.bereken_boekwaarde(item)
        item["afschrijving_per_jaar"] = asset_service.afschrijving_per_jaar(item)
    return jsonify(items)


@activa_bp.get("/<int:aid>")
def detail(aid):
    item = db.get_actief(current_app.config["DB_PATH"], aid)
    if item is None:
        return jsonify({"error": "Niet gevonden"}), 404
    item["boekwaarde"] = asset_service.bereken_boekwaarde(item)
    item["afschrijving_per_jaar"] = asset_service.afschrijving_per_jaar(item)
    item["afschrijvingsplan"] = asset_service.genereer_afschrijvingsplan(item)
    return jsonify(item)


@activa_bp.post("/")
def aanmaken():
    data = request.get_json(force=True)
    required = ["naam", "aanschafdatum", "aanschafwaarde"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Veld '{field}' is verplicht"}), 400
    aid = db.create_actief(current_app.config["DB_PATH"], data)
    return jsonify({"id": aid}), 201


@activa_bp.post("/<int:aid>/afschrijving")
def afschrijving_boeken(aid):
    data = request.get_json(force=True)
    data["actief_id"] = aid
    afid = db.create_afschrijving(current_app.config["DB_PATH"], data)
    return jsonify({"id": afid}), 201
