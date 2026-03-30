"""
BTW (VAT) service — all VAT calculations go through here.
Rules are read from config/tax_rules.json so they can be updated
without touching any Python code.
"""
import json
import os
import sqlite3
from decimal import Decimal, ROUND_HALF_UP


# ------------------------------------------------------------------ #
#  Config loader                                                       #
# ------------------------------------------------------------------ #

def load_tax_rules(config_dir: str) -> dict:
    path = os.path.join(config_dir, "tax_rules.json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_rate(tax_rules: dict, code: str) -> Decimal:
    """Return the Decimal rate for a BTW code like '21%', '9%', '0%', 'vrij', 'verlegd'."""
    mapping = {
        "21%":    "hoog",
        "9%":     "laag",
        "0%":     "nul",
        "vrij":   "vrijgesteld",
        "verlegd": "verlegd",
        "eu_b2c": "eu_b2c",
    }
    key = mapping.get(code, "hoog")
    rate = tax_rules["btw_tarieven"][key].get("rate")
    return Decimal(str(rate)) if rate is not None else Decimal("0")


# ------------------------------------------------------------------ #
#  Invoice line calculation                                            #
# ------------------------------------------------------------------ #

def bereken_factuurlijn(regel: dict, tax_rules: dict) -> dict:
    """
    Given a raw invoice line dict, calculate and return the completed line
    with btw_bedrag, totaal_excl, and totaal_incl populated.

    Expected keys in `regel`:
        hoeveelheid, eenheidsprijs, btw_tarief
    Optional:
        omschrijving, artikel_id, eenheid, grootboek_rekening
    """
    hoeveelheid   = Decimal(str(regel.get("hoeveelheid", 1)))
    eenheidsprijs = Decimal(str(regel.get("eenheidsprijs", 0)))
    btw_tarief    = regel.get("btw_tarief", "21%")
    btw_rate      = get_rate(tax_rules, btw_tarief)

    totaal_excl = (hoeveelheid * eenheidsprijs).quantize(Decimal("0.01"), ROUND_HALF_UP)
    btw_bedrag  = (totaal_excl * btw_rate).quantize(Decimal("0.01"), ROUND_HALF_UP)
    totaal_incl = totaal_excl + btw_bedrag

    return {
        **regel,
        "hoeveelheid":    float(hoeveelheid),
        "eenheidsprijs":  float(eenheidsprijs),
        "btw_tarief":     btw_tarief,
        "btw_bedrag":     float(btw_bedrag),
        "totaal_excl":    float(totaal_excl),
        "totaal_incl":    float(totaal_incl),
        "grootboek_rekening": regel.get("grootboek_rekening", "4000"),
    }


# ------------------------------------------------------------------ #
#  Invoice totals                                                      #
# ------------------------------------------------------------------ #

def bereken_factuur_totalen(regels: list[dict]) -> dict:
    """Sum up sales invoice lines into header totals by BTW band."""
    subtotaal = Decimal("0")
    btw_21    = Decimal("0")
    btw_9     = Decimal("0")
    btw_0     = Decimal("0")

    for r in regels:
        subtotaal += Decimal(str(r["totaal_excl"]))
        tarief = r["btw_tarief"]
        btw = Decimal(str(r["btw_bedrag"]))
        if tarief == "21%":
            btw_21 += btw
        elif tarief == "9%":
            btw_9 += btw
        elif tarief in ("0%", "vrij", "verlegd"):
            btw_0 += btw

    btw_totaal = btw_21 + btw_9 + btw_0
    totaal     = subtotaal + btw_totaal

    return {
        "subtotaal":  float(subtotaal.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "btw_21":     float(btw_21.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "btw_9":      float(btw_9.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "btw_0":      float(btw_0.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "btw_totaal": float(btw_totaal.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "totaal":     float(totaal.quantize(Decimal("0.01"), ROUND_HALF_UP)),
    }


def bereken_inkoop_totalen(regels: list[dict]) -> dict:
    """Sum up purchase invoice lines — single btw_bedrag field."""
    subtotaal  = Decimal("0")
    btw_totaal = Decimal("0")

    for r in regels:
        subtotaal  += Decimal(str(r["totaal_excl"]))
        btw_totaal += Decimal(str(r["btw_bedrag"]))

    totaal = subtotaal + btw_totaal
    return {
        "subtotaal":  float(subtotaal.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "btw_bedrag": float(btw_totaal.quantize(Decimal("0.01"), ROUND_HALF_UP)),
        "totaal":     float(totaal.quantize(Decimal("0.01"), ROUND_HALF_UP)),
    }


# ------------------------------------------------------------------ #
#  BTW aangifte (VAT return calculation)                              #
# ------------------------------------------------------------------ #

def bereken_btw_aangifte(db_path: str, config_dir: str,
                          periode: str, startdatum: str, einddatum: str,
                          periode_type: str) -> dict:
    """
    Compute BTW aangifte figures for a given date range.
    Returns a dict ready for upsert_btw_periode().

    Mapping to official Belastingdienst aangifte rubrieken:
      1a — 21% leveringen
      1b — 9%  leveringen
      3a — Export / 0%
      4a — Intra-EU B2B (verlegd)
      5b — Voorbelasting (inkoop-BTW)
    """
    tax_rules = load_tax_rules(config_dir)
    kor_actief = tax_rules["kor"]["actief"]

    from ..database.models import get_db, rows_to_list  # local import avoids circular

    with get_db(db_path) as conn:
        # ---- Verkoop (af te dragen) --------------------------------
        verkoop_regels = rows_to_list(conn.execute(
            """SELECT vr.btw_tarief, vr.totaal_excl, vr.btw_bedrag, vf.btw_type, vf.omgekeerde_heffing
               FROM verkoopfactuurregels vr
               JOIN verkoopfacturen vf ON vf.id = vr.factuur_id
               WHERE vf.factuurdatum BETWEEN ? AND ?
                 AND vf.status != 'gecrediteerd'""",
            (startdatum, einddatum)
        ).fetchall())

        # ---- Inkoop (voorbelasting) --------------------------------
        inkoop_regels = rows_to_list(conn.execute(
            """SELECT ir.btw_tarief, ir.totaal_excl, ir.btw_bedrag, inf.aftrekbaar_btw_pct
               FROM inkoopfactuurregels ir
               JOIN inkoopfacturen inf ON inf.id = ir.factuur_id
               WHERE inf.factuurdatum BETWEEN ? AND ?
                 AND inf.status != 'gecrediteerd'""",
            (startdatum, einddatum)
        ).fetchall())

        # ---- Platform kosten (omgekeerde heffing) ------------------
        platform_verlegd = rows_to_list(conn.execute(
            """SELECT bedrag_excl_btw, btw_tarief, omgekeerde_heffing
               FROM platform_kosten
               WHERE datum BETWEEN ? AND ? AND omgekeerde_heffing = 1""",
            (startdatum, einddatum)
        ).fetchall())

    # Aggregate verkoop
    omzet_21 = omzet_9 = omzet_0 = omzet_verlegd = omzet_eu_b2c = Decimal("0")
    btw_21   = btw_9   = btw_eu_b2c = btw_verlegd_af = Decimal("0")

    for r in verkoop_regels:
        excl = Decimal(str(r["totaal_excl"]))
        btw  = Decimal(str(r["btw_bedrag"]))
        tarief = r["btw_tarief"]
        btw_type = r.get("btw_type", "NL")
        omgekeerd = r.get("omgekeerde_heffing", 0)

        if omgekeerd:
            omzet_verlegd += excl
        elif btw_type == "EU_B2C":
            omzet_eu_b2c += excl
            btw_eu_b2c   += btw
        elif tarief == "21%":
            omzet_21 += excl
            btw_21   += btw
        elif tarief == "9%":
            omzet_9 += excl
            btw_9   += btw
        elif tarief in ("0%", "vrij"):
            omzet_0 += excl
        elif tarief == "verlegd":
            omzet_verlegd += excl

    # Omgekeerde heffing af te dragen (je draagt af as buyer in intra-EU)
    for p in platform_verlegd:
        bedrag = Decimal(str(p["bedrag_excl_btw"]))
        tarief = p.get("btw_tarief", "21%")
        rate = get_rate(tax_rules, tarief)
        btw_verlegd_af += (bedrag * rate).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # Aggregate voorbelasting (inkoop-BTW aftrekbaar)
    voorbelasting = Decimal("0")
    for r in inkoop_regels:
        btw = Decimal(str(r["btw_bedrag"]))
        pct = Decimal(str(r.get("aftrekbaar_btw_pct", 100))) / 100
        voorbelasting += (btw * pct).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # KOR: geen BTW afdragen als KOR actief
    if kor_actief:
        btw_21 = btw_9 = btw_eu_b2c = btw_verlegd_af = Decimal("0")
        voorbelasting = Decimal("0")

    totaal_af = btw_21 + btw_9 + btw_eu_b2c + btw_verlegd_af
    saldo = totaal_af - voorbelasting  # positief = te betalen; negatief = te vorderen

    def f(d: Decimal) -> float:
        return float(d.quantize(Decimal("0.01"), ROUND_HALF_UP))

    return {
        "periode":              periode,
        "type":                 periode_type,
        "startdatum":           startdatum,
        "einddatum":            einddatum,
        "status":               "concept",
        "omzet_21":             f(omzet_21),
        "btw_21_af":            f(btw_21),
        "omzet_9":              f(omzet_9),
        "btw_9_af":             f(btw_9),
        "omzet_0":              f(omzet_0),
        "omzet_verlegd":        f(omzet_verlegd),
        "btw_verlegd_af":       f(btw_verlegd_af),
        "omzet_eu_b2c":         f(omzet_eu_b2c),
        "btw_eu_b2c_af":        f(btw_eu_b2c),
        "voorbelasting_totaal": f(voorbelasting),
        "saldo_btw":            f(saldo),
        "kor_actief":           kor_actief,
    }
