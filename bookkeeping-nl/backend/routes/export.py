from flask import Blueprint, jsonify, request, current_app, send_file
from ..database import models as db
from ..services import export_service
import os

export_bp = Blueprint("export", __name__)


@export_bp.get("/verkoopfacturen/csv")
def export_verkoopfacturen():
    rows = db.get_verkoopfacturen(current_app.config["DB_PATH"])
    path = export_service.export_csv(
        rows,
        os.path.join(current_app.config["EXPORT_DIR"], "verkoopfacturen.csv")
    )
    return send_file(path, mimetype="text/csv", as_attachment=True,
                     download_name="verkoopfacturen.csv")


@export_bp.get("/inkoopfacturen/csv")
def export_inkoopfacturen():
    rows = db.get_inkoopfacturen(current_app.config["DB_PATH"])
    path = export_service.export_csv(
        rows,
        os.path.join(current_app.config["EXPORT_DIR"], "inkoopfacturen.csv")
    )
    return send_file(path, mimetype="text/csv", as_attachment=True,
                     download_name="inkoopfacturen.csv")


@export_bp.get("/kasboek/csv")
def export_kasboek():
    jaar = request.args.get("jaar", type=int)
    rows = db.get_kasboek(current_app.config["DB_PATH"], jaar)
    path = export_service.export_csv(
        rows,
        os.path.join(current_app.config["EXPORT_DIR"], "kasboek.csv")
    )
    return send_file(path, mimetype="text/csv", as_attachment=True,
                     download_name="kasboek.csv")


@export_bp.get("/platform/csv")
def export_platform():
    jaar = request.args.get("jaar", type=int)
    rows = db.get_platform_kosten(current_app.config["DB_PATH"], jaar)
    path = export_service.export_csv(
        rows,
        os.path.join(current_app.config["EXPORT_DIR"], "platform_kosten.csv")
    )
    return send_file(path, mimetype="text/csv", as_attachment=True,
                     download_name="platform_kosten.csv")


@export_bp.get("/kasboek/qif")
def export_kasboek_qif():
    """Export cashbook to QIF format — importable in GnuCash."""
    jaar = request.args.get("jaar", type=int)
    rows = db.get_kasboek(current_app.config["DB_PATH"], jaar)
    path = export_service.export_qif(
        rows,
        os.path.join(current_app.config["EXPORT_DIR"], "kasboek.qif")
    )
    return send_file(path, mimetype="application/qif", as_attachment=True,
                     download_name="kasboek.qif")


@export_bp.post("/importeren/csv")
def import_csv():
    """Import transactions from CSV (kasboek format)."""
    if "file" not in request.files:
        return jsonify({"error": "Geen bestand meegegeven"}), 400

    file = request.files["file"]
    tabel = request.form.get("tabel", "kasboek")
    db_path = current_app.config["DB_PATH"]

    try:
        result = export_service.import_csv(file, tabel, db_path)
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
