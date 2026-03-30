"""
Invoice number generation — sequential, year-based, prefix-configurable.
"""
import sqlite3
from datetime import datetime


def next_factuurnummer(db_path: str, instellingen: dict) -> str:
    """
    Generate the next invoice number based on settings.
    Format: {prefix}{YYYY}-{NNN}  e.g. F2026-001
    """
    prefix = instellingen.get("factuur_prefix", "F")
    jaar   = datetime.now().year

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT MAX(CAST(SUBSTR(factuurnummer, INSTR(factuurnummer, '-') + 1) AS INTEGER)) AS max_nr "
            "FROM verkoopfacturen WHERE factuurnummer LIKE ?",
            (f"{prefix}{jaar}-%",)
        ).fetchone()

    max_nr = row[0] if row and row[0] else 0
    next_nr = max_nr + 1
    return f"{prefix}{jaar}-{next_nr:03d}"
