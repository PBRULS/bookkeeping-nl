"""Integration tests for invoice creation and status flow hardening."""
import os
import sys
import tempfile

import pytest

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
        candidate = f"{path}{suffix}"
        try:
            if os.path.exists(candidate):
                os.remove(candidate)
        except PermissionError:
            pass


def create_sales_invoice(client, **overrides):
    payload = {
        "klant_naam": "Test Klant",
        "factuurdatum": "2026-03-01",
        "vervaldatum": "2026-03-31",
        "btw_type": "NL",
        "regels": [{
            "omschrijving": "Consulting",
            "hoeveelheid": 1,
            "eenheidsprijs": 100,
            "btw_tarief": "21%",
            "grootboek_rekening": "4000",
        }],
    }
    payload.update(overrides)
    response = client.post("/api/verkoopfacturen/", json=payload)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["id"]


def create_purchase_invoice(client, **overrides):
    payload = {
        "leverancier_naam": "Test Leverancier",
        "factuurdatum": "2026-03-01",
        "vervaldatum": "2026-03-31",
        "btw_type": "NL",
        "regels": [{
            "omschrijving": "Abonnement",
            "hoeveelheid": 1,
            "eenheidsprijs": 100,
            "btw_tarief": "21%",
            "grootboek_rekening": "5000",
        }],
    }
    payload.update(overrides)
    response = client.post("/api/inkoopfacturen/", json=payload)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["id"]


def test_sales_route_rejects_effectively_empty_lines():
    client, db_path = make_client()
    payload = {
        "klant_naam": "Test Klant",
        "factuurdatum": "2026-03-01",
        "vervaldatum": "2026-03-31",
        "regels": [{"omschrijving": "", "hoeveelheid": "", "eenheidsprijs": ""}],
    }

    response = client.post("/api/verkoopfacturen/", json=payload)

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "INVOICE_VALIDATION_FAILED"
    assert body["code"] == "EMPTY_INVOICE_LINES"
    cleanup_db(db_path)


def test_purchase_route_rejects_effectively_empty_lines():
    client, db_path = make_client()
    payload = {
        "leverancier_naam": "Test Leverancier",
        "factuurdatum": "2026-03-01",
        "vervaldatum": "2026-03-31",
        "regels": [{"omschrijving": "", "hoeveelheid": "", "eenheidsprijs": ""}],
    }

    response = client.post("/api/inkoopfacturen/", json=payload)

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "INVOICE_VALIDATION_FAILED"
    assert body["code"] == "EMPTY_INVOICE_LINES"
    cleanup_db(db_path)


def test_sales_route_rejects_invalid_export_tax_mix():
    client, db_path = make_client()
    payload = {
        "klant_naam": "Export Klant",
        "factuurdatum": "2026-03-01",
        "vervaldatum": "2026-03-31",
        "btw_type": "export",
        "regels": [{
            "omschrijving": "Exportregel",
            "hoeveelheid": 1,
            "eenheidsprijs": 100,
            "btw_tarief": "21%",
        }],
    }

    response = client.post("/api/verkoopfacturen/", json=payload)

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "INVOICE_VALIDATION_FAILED"
    assert body["code"] == "INVALID_SALES_TAX_COMBINATION"
    cleanup_db(db_path)


def test_purchase_route_rejects_invalid_eu_b2b_tax_mix():
    client, db_path = make_client()
    payload = {
        "leverancier_naam": "EU Leverancier",
        "factuurdatum": "2026-03-01",
        "vervaldatum": "2026-03-31",
        "btw_type": "EU_B2B",
        "regels": [{
            "omschrijving": "Dienst",
            "hoeveelheid": 1,
            "eenheidsprijs": 100,
            "btw_tarief": "21%",
        }],
    }

    response = client.post("/api/inkoopfacturen/", json=payload)

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "INVOICE_VALIDATION_FAILED"
    assert body["code"] == "INVALID_PURCHASE_TAX_COMBINATION"
    cleanup_db(db_path)


def test_sales_invoice_rounding_and_totals_are_persisted_consistently():
    client, db_path = make_client()
    invoice_id = create_sales_invoice(
        client,
        regels=[
            {
                "omschrijving": "Regel 1",
                "hoeveelheid": 3,
                "eenheidsprijs": 33.33,
                "btw_tarief": "21%",
            },
            {
                "omschrijving": "Regel 2",
                "hoeveelheid": 2,
                "eenheidsprijs": 19.99,
                "btw_tarief": "9%",
            },
        ],
    )

    response = client.get(f"/api/verkoopfacturen/{invoice_id}")
    body = response.get_json()

    assert response.status_code == 200
    assert body["subtotaal"] == pytest.approx(139.97)
    assert body["btw_21"] == pytest.approx(21.00)
    assert body["btw_9"] == pytest.approx(3.60)
    assert body["btw_totaal"] == pytest.approx(24.60)
    assert body["totaal"] == pytest.approx(164.57)
    assert body["regels"][0]["btw_bedrag"] == pytest.approx(21.00)
    assert body["regels"][1]["btw_bedrag"] == pytest.approx(3.60)
    cleanup_db(db_path)


def test_sales_status_flow_requires_full_amount_for_betaald():
    client, db_path = make_client()
    invoice_id = create_sales_invoice(client)

    response = client.patch(
        f"/api/verkoopfacturen/{invoice_id}/status",
        json={"status": "verzonden"},
    )
    assert response.status_code == 200

    response = client.patch(
        f"/api/verkoopfacturen/{invoice_id}/status",
        json={"status": "betaald", "betaald_bedrag": 50, "betalingsdatum": "2026-03-05"},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "INVOICE_VALIDATION_FAILED"
    assert body["code"] == "INVALID_STATUS_PAYMENT"
    cleanup_db(db_path)


def test_sales_status_flow_supports_partial_then_full_payment():
    client, db_path = make_client()
    invoice_id = create_sales_invoice(client)

    response = client.patch(f"/api/verkoopfacturen/{invoice_id}/status", json={"status": "verzonden"})
    assert response.status_code == 200

    response = client.patch(
        f"/api/verkoopfacturen/{invoice_id}/status",
        json={"status": "deels_betaald", "betaald_bedrag": 40, "betalingsdatum": "2026-03-06"},
    )
    assert response.status_code == 200

    response = client.patch(
        f"/api/verkoopfacturen/{invoice_id}/status",
        json={"status": "betaald", "betaald_bedrag": 121, "betalingsdatum": "2026-03-10"},
    )
    assert response.status_code == 200

    detail = client.get(f"/api/verkoopfacturen/{invoice_id}")
    body = detail.get_json()
    assert body["status"] == "betaald"
    assert body["betaald_bedrag"] == pytest.approx(121.00)
    assert body["betalingsdatum"] == "2026-03-10"
    cleanup_db(db_path)


def test_sales_status_flow_blocks_credit_after_paid():
    client, db_path = make_client()
    invoice_id = create_sales_invoice(client)

    assert client.patch(f"/api/verkoopfacturen/{invoice_id}/status", json={"status": "verzonden"}).status_code == 200
    assert client.patch(
        f"/api/verkoopfacturen/{invoice_id}/status",
        json={"status": "betaald", "betaald_bedrag": 121, "betalingsdatum": "2026-03-08"},
    ).status_code == 200

    response = client.patch(f"/api/verkoopfacturen/{invoice_id}/status", json={"status": "gecrediteerd"})

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "INVOICE_VALIDATION_FAILED"
    assert body["code"] == "INVALID_STATUS_TRANSITION"
    cleanup_db(db_path)


def test_purchase_status_flow_requires_clean_transition_and_payment_rules():
    client, db_path = make_client()
    invoice_id = create_purchase_invoice(client)

    response = client.patch(
        f"/api/inkoopfacturen/{invoice_id}/status",
        json={"status": "goedgekeurd", "betaald_bedrag": 10},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "INVOICE_VALIDATION_FAILED"
    assert body["code"] == "INVALID_STATUS_PAYMENT"

    response = client.patch(f"/api/inkoopfacturen/{invoice_id}/status", json={"status": "goedgekeurd"})
    assert response.status_code == 200

    response = client.patch(
        f"/api/inkoopfacturen/{invoice_id}/status",
        json={"status": "deels_betaald", "betaald_bedrag": 50, "betalingsdatum": "2026-03-07"},
    )
    assert response.status_code == 200

    response = client.patch(
        f"/api/inkoopfacturen/{invoice_id}/status",
        json={"status": "betaald", "betaald_bedrag": 121, "betalingsdatum": "2026-03-09"},
    )
    assert response.status_code == 200

    detail = client.get(f"/api/inkoopfacturen/{invoice_id}")
    body = detail.get_json()
    assert body["status"] == "betaald"
    assert body["betaald_bedrag"] == pytest.approx(121.00)
    cleanup_db(db_path)