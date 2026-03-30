from flask import Blueprint, jsonify, request, current_app
from ..database import models as db
from ..services import rgs_validation_service

kasboek_bp = Blueprint("kasboek", __name__)


@kasboek_bp.get("/")
def lijst():
    jaar = request.args.get("jaar", type=int)
    rekening_type = request.args.get("type")
    return jsonify(db.get_kasboek(current_app.config["DB_PATH"], jaar, rekening_type))


@kasboek_bp.post("/")
def aanmaken():
    data = request.get_json(force=True)
    required = ["datum", "categorie", "omschrijving", "bedrag"]
    for field in required:
        if data.get(field) is None:
            return jsonify({"error": f"Veld '{field}' is verplicht"}), 400

    rgs_rules = rgs_validation_service.load_rgs_rules(current_app.config["CONFIG_DIR"])
    rgs_validation_service.validate_cash_entry(data, rgs_rules)

    kid = db.create_kasboek_entry(current_app.config["DB_PATH"], data)
    return jsonify({"id": kid}), 201
