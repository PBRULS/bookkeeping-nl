"""
Invoice number generation — sequential, year-based, prefix-configurable.
"""
import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime


class InvoiceValidationError(ValueError):
    """Raised when invoice input or state transitions are inconsistent."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def normalize_invoice_lines(regels: list[dict] | None) -> list[dict]:
    normalized = []
    for regel in regels or []:
        if not isinstance(regel, dict):
            continue

        omschrijving = str(regel.get("omschrijving") or "").strip()
        hoeveelheid_raw = regel.get("hoeveelheid")
        prijs_raw = regel.get("eenheidsprijs")

        hoeveelheid_empty = hoeveelheid_raw in (None, "")
        prijs_empty = prijs_raw in (None, "")

        if not omschrijving and hoeveelheid_empty and prijs_empty:
            continue

        try:
            hoeveelheid = Decimal(
                str(1 if hoeveelheid_empty else hoeveelheid_raw)
            )
            eenheidsprijs = Decimal(str(0 if prijs_empty else prijs_raw))
        except Exception as exc:
            raise InvoiceValidationError(
                "INVALID_LINE_NUMBERS",
                "Factuurregel bevat een ongeldig aantal of prijs.",
            ) from exc

        if hoeveelheid <= 0:
            raise InvoiceValidationError(
                "INVALID_LINE_QUANTITY",
                "Factuurregel moet een hoeveelheid groter dan 0 hebben.",
            )

        if eenheidsprijs < 0:
            raise InvoiceValidationError(
                "INVALID_LINE_PRICE",
                "Factuurregel mag geen negatieve prijs hebben.",
            )

        normalized.append(
            {
                **regel,
                "omschrijving": omschrijving,
                "eenheid": str(regel.get("eenheid") or "stuk"),
                "hoeveelheid": float(
                    hoeveelheid.quantize(Decimal("0.01"), ROUND_HALF_UP)
                ),
                "eenheidsprijs": float(
                    eenheidsprijs.quantize(Decimal("0.01"), ROUND_HALF_UP)
                ),
            }
        )

    if not normalized:
        raise InvoiceValidationError(
            "EMPTY_INVOICE_LINES",
            "Factuur heeft minimaal één geldige regel nodig.",
        )

    return normalized


def validate_sales_tax_profile(
    regels: list[dict],
    btw_type: str,
    omgekeerde_heffing: bool,
) -> None:
    tarieven = {str(regel.get("btw_tarief") or "21%") for regel in regels}

    if omgekeerde_heffing or btw_type == "EU_B2B":
        invalid = tarieven - {"verlegd"}
        if invalid:
            raise InvoiceValidationError(
                "INVALID_SALES_TAX_COMBINATION",
                (
                    "EU B2B / verlegd-verkoop mag alleen regels "
                    "met tarief 'verlegd' bevatten."
                ),
            )
        return

    if btw_type == "export":
        invalid = tarieven - {"0%"}
        if invalid:
            raise InvoiceValidationError(
                "INVALID_SALES_TAX_COMBINATION",
                "Exportfacturen mogen alleen regels met tarief '0%' bevatten.",
            )
        return

    if btw_type == "NL" and "verlegd" in tarieven:
        raise InvoiceValidationError(
            "INVALID_SALES_TAX_COMBINATION",
            "Tarief 'verlegd' vereist BTW-type EU_B2B of omgekeerde heffing.",
        )

    if btw_type == "EU_B2C" and "verlegd" in tarieven:
        raise InvoiceValidationError(
            "INVALID_SALES_TAX_COMBINATION",
            "EU B2C (OSS) mag geen regels met tarief 'verlegd' bevatten.",
        )


def validate_purchase_tax_profile(regels: list[dict], btw_type: str) -> None:
    tarieven = {str(regel.get("btw_tarief") or "21%") for regel in regels}

    if btw_type == "import":
        invalid = tarieven - {"0%"}
        if invalid:
            raise InvoiceValidationError(
                "INVALID_PURCHASE_TAX_COMBINATION",
                (
                    "Import-inkoopfacturen mogen alleen regels "
                    "met tarief '0%' bevatten."
                ),
            )
        return

    if btw_type == "EU_B2B":
        invalid = tarieven - {"verlegd"}
        if invalid:
            raise InvoiceValidationError(
                "INVALID_PURCHASE_TAX_COMBINATION",
                (
                    "EU B2B-inkoopfacturen mogen alleen regels "
                    "met tarief 'verlegd' bevatten."
                ),
            )
        return

    if btw_type == "NL" and "verlegd" in tarieven:
        raise InvoiceValidationError(
            "INVALID_PURCHASE_TAX_COMBINATION",
            "Tarief 'verlegd' vereist BTW-type EU_B2B bij inkoopfacturen.",
        )


def validate_status_transition(
    current_status: str,
    new_status: str,
    totaal: float,
    current_paid: float,
    current_payment_date: str | None,
    betaald_bedrag: float | None,
    betalingsdatum: str | None,
    allowed_transitions: dict[str, set[str]],
) -> tuple[float, str | None]:
    if new_status not in allowed_transitions.get(current_status, set()):
        raise InvoiceValidationError(
            "INVALID_STATUS_TRANSITION",
            (
                f"Statusovergang van '{current_status}' "
                f"naar '{new_status}' is niet toegestaan."
            ),
        )

    totaal_decimal = Decimal(str(totaal or 0)).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
    current_paid_decimal = Decimal(str(current_paid or 0)).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
    if betaald_bedrag is None:
        next_paid = current_paid_decimal
    else:
        next_paid = Decimal(str(betaald_bedrag)).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
    next_payment_date = betalingsdatum or current_payment_date

    if next_paid < 0:
        raise InvoiceValidationError(
            "INVALID_PAYMENT_AMOUNT",
            "Betaald bedrag kan niet negatief zijn.",
        )

    if next_paid > totaal_decimal:
        raise InvoiceValidationError(
            "INVALID_PAYMENT_AMOUNT",
            "Betaald bedrag kan niet hoger zijn dan het factuurtotaal.",
        )

    if new_status == "betaald":
        if next_paid != totaal_decimal:
            raise InvoiceValidationError(
                "INVALID_STATUS_PAYMENT",
                (
                    "Status 'betaald' vereist een betaald bedrag "
                    "gelijk aan het factuurtotaal."
                ),
            )
        if not next_payment_date:
            raise InvoiceValidationError(
                "MISSING_PAYMENT_DATE",
                "Status 'betaald' vereist een betalingsdatum.",
            )

    if (
        new_status == "deels_betaald"
        and not (Decimal("0.00") < next_paid < totaal_decimal)
    ):
        raise InvoiceValidationError(
            "INVALID_STATUS_PAYMENT",
            (
                "Status 'deels_betaald' vereist een betaald bedrag "
                "groter dan 0 en kleiner dan het factuurtotaal."
            ),
        )

    if (
        new_status in {"concept", "verzonden", "ontvangen", "goedgekeurd", "verlopen"}
        and next_paid > 0
    ):
        raise InvoiceValidationError(
            "INVALID_STATUS_PAYMENT",
            f"Status '{new_status}' staat geen betaald bedrag groter dan 0 toe.",
        )

    if new_status == "gecrediteerd" and current_status == "betaald":
        raise InvoiceValidationError(
            "INVALID_STATUS_TRANSITION",
            (
                "Een volledig betaalde factuur kan niet direct "
                "naar 'gecrediteerd' zonder aparte correctiestap."
            ),
        )

    return float(next_paid), next_payment_date


def next_factuurnummer(db_path: str, instellingen: dict) -> str:
    """
    Generate the next invoice number based on settings.
    Format: {prefix}{YYYY}-{NNN}  e.g. F2026-001
    """
    prefix = instellingen.get("factuur_prefix", "F")
    jaar = datetime.now().year

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            (
                "SELECT MAX(CAST(SUBSTR(factuurnummer, "
                "INSTR(factuurnummer, '-') + 1) AS INTEGER)) AS max_nr "
                "FROM verkoopfacturen WHERE factuurnummer LIKE ?"
            ),
            (f"{prefix}{jaar}-%",)
        ).fetchone()

    max_nr = row[0] if row and row[0] else 0
    next_nr = max_nr + 1
    return f"{prefix}{jaar}-{next_nr:03d}"
