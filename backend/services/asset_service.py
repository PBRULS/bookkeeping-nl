"""
Fixed asset service — depreciation calculations.
"""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP


def _aanschaf_date(actief: dict) -> date:
    ds = actief.get("aanschafdatum", "")
    try:
        return datetime.strptime(ds[:10], "%Y-%m-%d").date()
    except ValueError:
        return date.today()


def afschrijving_per_jaar(actief: dict) -> float:
    aanschaf  = Decimal(str(actief.get("aanschafwaarde", 0)))
    restwaarde = Decimal(str(actief.get("restwaarde", 0)))
    jaren     = int(actief.get("afschrijvingsjaren", 5) or 5)
    methode   = actief.get("afschrijvingsmethode", "lineair")

    if jaren == 0:
        return 0.0

    if methode == "lineair":
        bedrag = (aanschaf - restwaarde) / Decimal(jaren)
    else:
        # Degressief: 2× lineaire afschrijvingspercentage op boekwaarde
        pct = Decimal("2") / Decimal(jaren)
        bedrag = aanschaf * pct  # first year; simplified for plan generation

    return float(bedrag.quantize(Decimal("0.01"), ROUND_HALF_UP))


def bereken_boekwaarde(actief: dict) -> float:
    """Current book value = aanschafwaarde minus total depreciation booked."""
    aanschaf = Decimal(str(actief.get("aanschafwaarde", 0)))
    afschr_geboekt = sum(
        Decimal(str(a.get("bedrag", 0)))
        for a in actief.get("afschrijvingen", [])
    )
    restwaarde = Decimal(str(actief.get("restwaarde", 0)))
    boekwaarde = max(aanschaf - afschr_geboekt, restwaarde)
    return float(boekwaarde.quantize(Decimal("0.01"), ROUND_HALF_UP))


def genereer_afschrijvingsplan(actief: dict) -> list[dict]:
    """Generate a full depreciation schedule for the asset."""
    aanschaf    = Decimal(str(actief.get("aanschafwaarde", 0)))
    restwaarde  = Decimal(str(actief.get("restwaarde", 0)))
    jaren       = int(actief.get("afschrijvingsjaren", 5) or 5)
    methode     = actief.get("afschrijvingsmethode", "lineair")
    start_date  = _aanschaf_date(actief)

    plan = []
    boekwaarde = aanschaf

    for i in range(jaren):
        jaar = start_date.year + i

        if methode == "lineair":
            afschrijving = (aanschaf - restwaarde) / Decimal(jaren)
        else:
            pct = Decimal("2") / Decimal(jaren)
            afschrijving = (boekwaarde - restwaarde) * pct

        afschrijving = afschrijving.quantize(Decimal("0.01"), ROUND_HALF_UP)
        boekwaarde   = max(boekwaarde - afschrijving, restwaarde)

        plan.append({
            "jaar":          jaar,
            "afschrijving":  float(afschrijving),
            "boekwaarde_na": float(boekwaarde),
        })

        if boekwaarde <= restwaarde:
            break

    return plan
