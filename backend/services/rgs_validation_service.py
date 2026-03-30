"""RGS validation service for transaction posting rules."""
import json
import os
from dataclasses import dataclass


@dataclass
class RgsValidationError(ValueError):
    code: str
    message: str
    details: list[dict] | None = None

    def __str__(self) -> str:
        return self.message


def load_rgs_rules(config_dir: str) -> dict:
    path = os.path.join(config_dir, "rgs_rules.json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _raise(code: str, message: str, details: list[dict] | None = None) -> None:
    raise RgsValidationError(code=code, message=message, details=details or [])


def validate_sales_lines(lines: list[dict], rgs_rules: dict) -> None:
    cfg = rgs_rules["sales_invoice_line"]
    allowed_credit = set(cfg["allowed_credit_accounts"])
    vat_map = cfg["vat_credit_accounts"]

    violations: list[dict] = []
    for idx, line in enumerate(lines, start=1):
        credit = str(line.get("grootboek_rekening") or "4000")
        vat_code = str(line.get("btw_tarief") or "21%")

        if credit not in allowed_credit:
            violations.append({
                "line": idx,
                "field": "grootboek_rekening",
                "value": credit,
                "reason": "Niet toegestaan voor verkoopregel volgens RGS-rules"
            })

        if vat_code not in vat_map:
            violations.append({
                "line": idx,
                "field": "btw_tarief",
                "value": vat_code,
                "reason": "Onbekend BTW-tarief voor RGS-rules"
            })

    if violations:
        _raise("RGS_SALES_INVALID", "RGS-validatie mislukt voor verkoopfactuurregels", violations)


def validate_purchase_lines(lines: list[dict], rgs_rules: dict) -> None:
    cfg = rgs_rules["purchase_invoice_line"]
    allowed_debit = set(cfg["allowed_debit_accounts"])
    vat_map = cfg["vat_debit_accounts"]

    violations: list[dict] = []
    for idx, line in enumerate(lines, start=1):
        debit = str(line.get("grootboek_rekening") or "5000")
        vat_code = str(line.get("btw_tarief") or "21%")

        if debit not in allowed_debit:
            violations.append({
                "line": idx,
                "field": "grootboek_rekening",
                "value": debit,
                "reason": "Niet toegestaan voor inkoopregel volgens RGS-rules"
            })

        if vat_code not in vat_map:
            violations.append({
                "line": idx,
                "field": "btw_tarief",
                "value": vat_code,
                "reason": "Onbekend BTW-tarief voor RGS-rules"
            })

    if violations:
        _raise("RGS_PURCHASE_INVALID", "RGS-validatie mislukt voor inkoopfactuurregels", violations)


def validate_cash_entry(entry: dict, rgs_rules: dict) -> None:
    category = str(entry.get("categorie") or "").strip()
    rekening_type = str(entry.get("rekening_type") or "bank").strip()
    mapping = rgs_rules["rekening_type_to_account"]

    if rekening_type not in mapping:
        _raise("RGS_CASH_INVALID", f"Onbekend rekening_type: {rekening_type}")

    bank_or_cash_account = mapping[rekening_type]
    provided_account = str(
        entry.get("grootboek_rekening") or entry.get("tegenrekening") or ""
    ).strip()

    if category == "ontvangst":
        cfg = rgs_rules["cash_receipt"]
        debit = bank_or_cash_account
        credit = provided_account or cfg["default_credit_account"]
        if debit not in set(cfg["allowed_debit_accounts"]):
            _raise("RGS_CASH_INVALID", "Debetrekening niet toegestaan voor ontvangst", [{"debet": debit}])
        if credit not in set(cfg["allowed_credit_accounts"]):
            _raise("RGS_CASH_INVALID", "Creditrekening niet toegestaan voor ontvangst", [{"credit": credit}])

    elif category == "uitgave":
        cfg = rgs_rules["cash_payment"]
        debit = provided_account or cfg["default_debit_account"]
        credit = bank_or_cash_account
        if debit not in set(cfg["allowed_debit_accounts"]):
            _raise("RGS_CASH_INVALID", "Debetrekening niet toegestaan voor uitgave", [{"debet": debit}])
        if credit not in set(cfg["allowed_credit_accounts"]):
            _raise("RGS_CASH_INVALID", "Creditrekening niet toegestaan voor uitgave", [{"credit": credit}])

    else:
        _raise("RGS_CASH_INVALID", f"Onbekende kasboek categorie: {category}")
