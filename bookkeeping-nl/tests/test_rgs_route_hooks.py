"""Integration tests for route-level RGS hook behavior."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app import create_app
from backend.database.init_db import init_database


def make_client():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    init_database(tmp.name)

    app = create_app(tmp.name)
    app.config["TESTING"] = True
    client = app.test_client()
    return client, tmp.name


def cleanup_db(path: str) -> None:
    for suffix in ("", "-wal", "-shm"):
        p = f"{path}{suffix}"
        try:
            if os.path.exists(p):
                os.remove(p)
        except PermissionError:
            pass


def test_sales_route_rejects_invalid_rgs_account():
    client, db_path = make_client()
    payload = {
        "klant_naam": "Test Klant",
        "factuurdatum": "2026-03-01",
        "vervaldatum": "2026-03-31",
        "regels": [
            {
                "omschrijving": "Onjuiste regel",
                "hoeveelheid": 1,
                "eenheidsprijs": 100,
                "btw_tarief": "21%",
                "grootboek_rekening": "6100"
            }
        ]
    }
    resp = client.post("/api/verkoopfacturen/", json=payload)
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "RGS_VALIDATION_FAILED"
    cleanup_db(db_path)


def test_cash_route_rejects_invalid_rgs_account():
    client, db_path = make_client()
    payload = {
        "datum": "2026-03-01",
        "rekening_type": "bank",
        "categorie": "uitgave",
        "omschrijving": "Onjuist",
        "bedrag": 25,
        "grootboek_rekening": "4000"
    }
    resp = client.post("/api/kasboek/", json=payload)
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "RGS_VALIDATION_FAILED"
    cleanup_db(db_path)
