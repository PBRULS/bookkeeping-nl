from flask import Blueprint, jsonify, request, current_app
from ..database import models as db

platform_bp = Blueprint("platform", __name__)


@platform_bp.get("/")
def lijst():
    jaar = request.args.get("jaar", type=int)
    return jsonify(db.get_platform_kosten(current_app.config["DB_PATH"], jaar))


@platform_bp.post("/")
def aanmaken():
    data = request.get_json(force=True)
    required = ["datum", "platform", "type", "bedrag_excl_btw"]
    for field in required:
        if data.get(field) is None:
            return jsonify({"error": f"Veld '{field}' is verplicht"}), 400

    # Calculate total
    bedrag = float(data["bedrag_excl_btw"])
    btw_tarief = data.get("btw_tarief", "21%")
    omgekeerde_heffing = data.get("omgekeerde_heffing", False)

    if omgekeerde_heffing:
        btw_bedrag = 0.0
    elif btw_tarief == "21%":
        btw_bedrag = round(bedrag * 0.21, 2)
    elif btw_tarief == "9%":
        btw_bedrag = round(bedrag * 0.09, 2)
    else:
        btw_bedrag = 0.0

    data["btw_bedrag"] = btw_bedrag
    data["totaal"] = round(bedrag + btw_bedrag, 2)
    data["omgekeerde_heffing"] = 1 if omgekeerde_heffing else 0

    pid = db.create_platform_kost(current_app.config["DB_PATH"], data)
    return jsonify({"id": pid}), 201
