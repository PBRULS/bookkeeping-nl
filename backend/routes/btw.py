from flask import Blueprint, jsonify, request, current_app
from ..database import models as db
from ..services import vat_service

btw_bp = Blueprint("btw", __name__)


@btw_bp.get("/periodes")
def periodes():
    return jsonify(db.get_btw_periodes(current_app.config["DB_PATH"]))


@btw_bp.post("/berekenen")
def berekenen():
    """Calculate a VAT period from invoice data and save as 'concept'."""
    data = request.get_json(force=True)
    db_path = current_app.config["DB_PATH"]
    config_dir = current_app.config["CONFIG_DIR"]

    periode_id = data.get("periode")      # e.g. "2026-Q1"
    startdatum  = data.get("startdatum")  # e.g. "2026-01-01"
    einddatum   = data.get("einddatum")   # e.g. "2026-03-31"
    periode_type = data.get("type", "kwartaal")

    if not all([periode_id, startdatum, einddatum]):
        return jsonify({"error": "Veld 'periode', 'startdatum' en 'einddatum' zijn verplicht"}), 400

    aangifte = vat_service.bereken_btw_aangifte(
        db_path, config_dir, periode_id, startdatum, einddatum, periode_type
    )
    db.upsert_btw_periode(db_path, aangifte)
    return jsonify(aangifte)


@btw_bp.patch("/periodes/<periode_id>/status")
def update_status(periode_id):
    data = request.get_json(force=True)
    allowed = {"open", "concept", "ingediend", "betaald"}
    status = data.get("status")
    if status not in allowed:
        return jsonify({"error": f"Ongeldige status: {status}"}), 400

    db_path = current_app.config["DB_PATH"]
    with db.get_db(db_path) as conn:
        conn.execute(
            "UPDATE btw_periodes SET status=? WHERE periode=?", (status, periode_id)
        )
        conn.commit()
    return jsonify({"ok": True})


@btw_bp.get("/tarieven")
def tarieven():
    """Return current tax rates from config — for the frontend dropdowns."""
    tax_rules = vat_service.load_tax_rules(current_app.config["CONFIG_DIR"])
    return jsonify(tax_rules.get("btw_tarieven", {}))
