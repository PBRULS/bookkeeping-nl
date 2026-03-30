"""
Export service — CSV, QIF output and CSV import.
GnuCash can import QIF files directly.
"""
import csv
import io
import os
from datetime import datetime
from typing import IO


# ------------------------------------------------------------------ #
#  CSV Export                                                          #
# ------------------------------------------------------------------ #

def export_csv(rows: list[dict], output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not rows:
        with open(output_path, "w", newline="", encoding="utf-8-sig") as fh:
            fh.write("")
        return output_path

    with open(output_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()),
                                delimiter=";", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


# ------------------------------------------------------------------ #
#  QIF Export (GnuCash compatible)                                    #
# ------------------------------------------------------------------ #

def export_qif(kasboek_rows: list[dict], output_path: str) -> str:
    """
    Export kasboek entries to QIF (Quicken Interchange Format).
    GnuCash: File > Import > Import QIF...
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("!Type:Bank\n")
        for row in kasboek_rows:
            datum = _format_qif_date(row.get("datum", ""))
            bedrag = float(row.get("bedrag", 0))
            if row.get("categorie") == "uitgave":
                bedrag = -abs(bedrag)
            else:
                bedrag = abs(bedrag)

            fh.write(f"D{datum}\n")
            fh.write(f"T{bedrag:.2f}\n")
            fh.write(f"P{row.get('omschrijving', '')}\n")
            if row.get("tegenrekening"):
                fh.write(f"L{row['tegenrekening']}\n")
            fh.write("^\n")

    return output_path


def _format_qif_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to MM/DD/YYYY (QIF standard)."""
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return d.strftime("%m/%d/%Y")
    except ValueError:
        return date_str


# ------------------------------------------------------------------ #
#  CSV Import                                                          #
# ------------------------------------------------------------------ #

KASBOEK_REQUIRED_COLS = {"datum", "categorie", "omschrijving", "bedrag"}


def import_csv(file: IO, tabel: str, db_path: str) -> dict:
    """
    Parse an uploaded CSV and insert rows into the database.
    Supported tables: kasboek
    Returns {"imported": N, "skipped": M, "errors": [...]}
    """
    from ..database import models as db_models

    content = file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")

    imported = 0
    skipped  = 0
    errors   = []

    if tabel == "kasboek":
        for i, row in enumerate(reader, start=2):
            missing = KASBOEK_REQUIRED_COLS - set(row.keys())
            if missing:
                errors.append(f"Rij {i}: ontbrekende kolommen {missing}")
                skipped += 1
                continue
            try:
                row["bedrag"] = float(str(row["bedrag"]).replace(",", "."))
                db_models.create_kasboek_entry(db_path, row)
                imported += 1
            except Exception as exc:
                errors.append(f"Rij {i}: {exc}")
                skipped += 1
    else:
        raise ValueError(f"Importeren naar tabel '{tabel}' wordt niet ondersteund.")

    return {"imported": imported, "skipped": skipped, "errors": errors}
