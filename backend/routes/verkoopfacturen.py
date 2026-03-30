from flask import Blueprint, jsonify, request, current_app
from ..database import models as db
from ..services import invoice_service, vat_service
from ..services import rgs_validation_service

verkoopfacturen_bp = Blueprint("verkoopfacturen", __name__)


@verkoopfacturen_bp.get("/")
def lijst():
    status = request.args.get("status")
    return jsonify(db.get_verkoopfacturen(current_app.config["DB_PATH"], status))


@verkoopfacturen_bp.get("/<int:fid>")
def detail(fid):
    item = db.get_verkoopfactuur(current_app.config["DB_PATH"], fid)
    if item is None:
        return jsonify({"error": "Niet gevonden"}), 404
    return jsonify(item)


@verkoopfacturen_bp.post("/")
def aanmaken():
    data = request.get_json(force=True)
    regels = data.pop("regels", [])

    if not regels:
        return jsonify({"error": "Factuur heeft minimaal één regel nodig"}), 400

    db_path = current_app.config["DB_PATH"]
    tax_rules = vat_service.load_tax_rules(current_app.config["CONFIG_DIR"])

    # Auto-generate invoice number if not provided
    if not data.get("factuurnummer"):
        instellingen = db.get_all_instellingen(db_path)
        data["factuurnummer"] = invoice_service.next_factuurnummer(db_path, instellingen)

    # Calculate VAT on each rule
    calculated_regels = []
    for regel in regels:
        calculated_regels.append(vat_service.bereken_factuurlijn(regel, tax_rules))

    # Calculate invoice totals
    totals = vat_service.bereken_factuur_totalen(calculated_regels)
    data.update(totals)

    # Validate posting logic against configured RGS rules before save.
    rgs_rules = rgs_validation_service.load_rgs_rules(current_app.config["CONFIG_DIR"])
    rgs_validation_service.validate_sales_lines(calculated_regels, rgs_rules)

    fid = db.create_verkoopfactuur(db_path, data, calculated_regels)
    return jsonify({"id": fid, "factuurnummer": data["factuurnummer"]}), 201


@verkoopfacturen_bp.patch("/<int:fid>/status")
def update_status(fid):
    data = request.get_json(force=True)
    allowed = {"concept", "verzonden", "betaald", "deels_betaald", "verlopen", "gecrediteerd"}
    status = data.get("status")
    if status not in allowed:
        return jsonify({"error": f"Ongeldige status: {status}"}), 400
    db.update_verkoopfactuur_status(
        current_app.config["DB_PATH"], fid, status,
        data.get("betaald_bedrag"), data.get("betalingsdatum")
    )
    return jsonify({"ok": True})
