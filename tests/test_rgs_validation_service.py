"""Unit tests for RGS validation service."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.services import rgs_validation_service as rgs


CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")


def rules() -> dict:
    return rgs.load_rgs_rules(CONFIG_DIR)


def test_sales_valid():
    lines = [{"grootboek_rekening": "4000", "btw_tarief": "21%"}]
    rgs.validate_sales_lines(lines, rules())


def test_sales_invalid_account():
    lines = [{"grootboek_rekening": "6100", "btw_tarief": "21%"}]
    with pytest.raises(rgs.RgsValidationError) as exc:
        rgs.validate_sales_lines(lines, rules())
    assert exc.value.code == "RGS_SALES_INVALID"


def test_purchase_valid():
    lines = [{"grootboek_rekening": "6100", "btw_tarief": "9%"}]
    rgs.validate_purchase_lines(lines, rules())


def test_purchase_invalid_account():
    lines = [{"grootboek_rekening": "4000", "btw_tarief": "9%"}]
    with pytest.raises(rgs.RgsValidationError) as exc:
        rgs.validate_purchase_lines(lines, rules())
    assert exc.value.code == "RGS_PURCHASE_INVALID"


def test_cash_receipt_valid_default_counter_account():
    entry = {
        "rekening_type": "bank",
        "categorie": "ontvangst",
        "omschrijving": "betaling klant",
        "bedrag": 100.0,
    }
    rgs.validate_cash_entry(entry, rules())


def test_cash_payment_invalid_debit_account():
    entry = {
        "rekening_type": "bank",
        "categorie": "uitgave",
        "omschrijving": "onjuiste rekening",
        "bedrag": 50.0,
        "grootboek_rekening": "4000",
    }
    with pytest.raises(rgs.RgsValidationError) as exc:
        rgs.validate_cash_entry(entry, rules())
    assert exc.value.code == "RGS_CASH_INVALID"
