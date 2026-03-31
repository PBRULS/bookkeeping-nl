from flask import Blueprint, jsonify, request, current_app
from ..database import models as db
from ..services import vat_service
from ..services.invoice_service import (
    normalize_invoice_lines,
    validate_purchase_tax_profile,
)
from ..services import rgs_validation_service

inkoopfacturen_bp = Blueprint("inkoopfacturen", __name__)


@inkoopfacturen_bp.get("/")
def lijst():
    status = request.args.get("status")
    return jsonify(
        db.get_inkoopfacturen(current_app.config["DB_PATH"], status)
    )


@inkoopfacturen_bp.get("/<int:fid>")
def detail(fid):
    item = db.get_inkoopfactuur(current_app.config["DB_PATH"], fid)
    if item is None:
        return jsonify({"error": "Niet gevonden"}), 404
    return jsonify(item)


@inkoopfacturen_bp.post("/")
def aanmaken():
    data = request.get_json(force=True)
    raw_regels = data.pop("regels", [])

    if not data.get("leverancier_naam"):
        return jsonify({"error": "Veld 'leverancier_naam' is verplicht"}), 400
    if not data.get("factuurdatum"):
        return jsonify({"error": "Veld 'factuurdatum' is verplicht"}), 400

    db_path = current_app.config["DB_PATH"]
    tax_rules = vat_service.load_tax_rules(current_app.config["CONFIG_DIR"])
    regels = normalize_invoice_lines(raw_regels)
    validate_purchase_tax_profile(
        regels,
        str(data.get("btw_type") or "NL"),
    )

    calculated_regels = [
        vat_service.bereken_factuurlijn(regel, tax_rules)
        for regel in regels
    ]
    totals = vat_service.bereken_inkoop_totalen(calculated_regels)
    data.update(totals)

    # Validate posting logic against configured RGS rules before save.
    rgs_rules = rgs_validation_service.load_rgs_rules(
        current_app.config["CONFIG_DIR"]
    )
    rgs_validation_service.validate_purchase_lines(
        calculated_regels,
        rgs_rules,
    )

    fid = db.create_inkoopfactuur(db_path, data, calculated_regels)
    return jsonify({"id": fid}), 201


@inkoopfacturen_bp.patch("/<int:fid>/status")
def update_status(fid):
    data = request.get_json(force=True)
    allowed = {
        "ontvangen",
        "goedgekeurd",
        "betaald",
        "deels_betaald",
        "gecrediteerd",
    }
    status = data.get("status")
    if status not in allowed:
        return jsonify({"error": f"Ongeldige status: {status}"}), 400

    if db.get_inkoopfactuur(current_app.config["DB_PATH"], fid) is None:
        return jsonify({"error": "Niet gevonden"}), 404

    db.update_inkoopfactuur_status(
        current_app.config["DB_PATH"],
        fid,
        status,
        data.get("betaald_bedrag"),
        data.get("betalingsdatum"),
    )
    return jsonify({"ok": True})
