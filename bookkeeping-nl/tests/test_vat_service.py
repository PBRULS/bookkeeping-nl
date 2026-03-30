"""Tests for VAT (BTW) calculation service."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from backend.services.vat_service import bereken_factuurlijn, bereken_factuur_totalen, get_rate

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")


def tax_rules():
    from backend.services.vat_service import load_tax_rules
    return load_tax_rules(CONFIG_DIR)


# ---- get_rate -----------------------------------------------------------

def test_get_rate_21():
    assert float(get_rate(tax_rules(), "21%")) == pytest.approx(0.21)

def test_get_rate_9():
    assert float(get_rate(tax_rules(), "9%")) == pytest.approx(0.09)

def test_get_rate_0():
    assert float(get_rate(tax_rules(), "0%")) == pytest.approx(0.0)

def test_get_rate_vrij():
    assert float(get_rate(tax_rules(), "vrij")) == pytest.approx(0.0)

def test_get_rate_verlegd():
    assert float(get_rate(tax_rules(), "verlegd")) == pytest.approx(0.0)

def test_lijn_21_pct():
    regel = {"hoeveelheid": 2, "eenheidsprijs": 100.00, "btw_tarief": "21%"}
    result = bereken_factuurlijn(regel, tax_rules())
    assert result["totaal_excl"]  == pytest.approx(200.00)
    assert result["btw_bedrag"]   == pytest.approx(42.00)
    assert result["totaal_incl"]  == pytest.approx(242.00)

def test_lijn_9_pct():
    regel = {"hoeveelheid": 1, "eenheidsprijs": 50.00, "btw_tarief": "9%"}
    result = bereken_factuurlijn(regel, tax_rules())
    assert result["btw_bedrag"]   == pytest.approx(4.50)
    assert result["totaal_incl"]  == pytest.approx(54.50)

def test_lijn_export_0_pct():
    regel = {"hoeveelheid": 5, "eenheidsprijs": 20.00, "btw_tarief": "0%"}
    result = bereken_factuurlijn(regel, tax_rules())
    assert result["btw_bedrag"]   == pytest.approx(0.00)
    assert result["totaal_incl"]  == pytest.approx(100.00)

def test_lijn_verlegd():
    """Intra-EU B2B reversed charge — no VAT charged on invoice."""
    regel = {"hoeveelheid": 1, "eenheidsprijs": 1000.00, "btw_tarief": "verlegd"}
    result = bereken_factuurlijn(regel, tax_rules())
    assert result["btw_bedrag"]  == pytest.approx(0.00)
    assert result["totaal_incl"] == pytest.approx(1000.00)

def test_lijn_rounding():
    """Cent rounding: 3 × €33.33 = €99.99, BTW 21% = €20.9979 → rounds to €21.00."""
    regel = {"hoeveelheid": 3, "eenheidsprijs": 33.33, "btw_tarief": "21%"}
    result = bereken_factuurlijn(regel, tax_rules())
    assert result["totaal_excl"] == pytest.approx(99.99)
    assert result["btw_bedrag"]  == pytest.approx(21.00)


# ---- bereken_factuur_totalen --------------------------------------------

def test_totalen_mixed():
    regels = [
        bereken_factuurlijn({"hoeveelheid": 1, "eenheidsprijs": 100, "btw_tarief": "21%"}, tax_rules()),
        bereken_factuurlijn({"hoeveelheid": 1, "eenheidsprijs": 50,  "btw_tarief": "9%"},  tax_rules()),
        bereken_factuurlijn({"hoeveelheid": 1, "eenheidsprijs": 200, "btw_tarief": "0%"},  tax_rules()),
    ]
    totalen = bereken_factuur_totalen(regels)
    assert totalen["subtotaal"]  == pytest.approx(350.00)
    assert totalen["btw_21"]     == pytest.approx(21.00)
    assert totalen["btw_9"]      == pytest.approx(4.50)
    assert totalen["btw_0"]      == pytest.approx(0.00)
    assert totalen["btw_totaal"] == pytest.approx(25.50)
    assert totalen["totaal"]     == pytest.approx(375.50)
