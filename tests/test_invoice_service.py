"""Tests for invoice number generation."""
import sqlite3
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.services.invoice_service import next_factuurnummer
from backend.database.init_db import init_database


def make_db():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    init_database(tmp.name)
    return tmp.name


def cleanup_db(path: str) -> None:
    for suffix in ("", "-wal", "-shm"):
        p = f"{path}{suffix}"
        try:
            if os.path.exists(p):
                os.remove(p)
        except PermissionError:
            # Windows can keep file handles briefly; tests should not fail on cleanup.
            pass


def test_first_number():
    db = make_db()
    instellingen = {"factuur_prefix": "F", "factuur_startnum": "1"}
    nr = next_factuurnummer(db, instellingen)
    year = __import__("datetime").datetime.now().year
    assert nr == f"F{year}-001"
    cleanup_db(db)


def test_sequential():
    db = make_db()
    instellingen = {"factuur_prefix": "F"}
    year = __import__("datetime").datetime.now().year

    # Manually insert a dummy invoice
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO verkoopfacturen (factuurnummer, klant_naam, factuurdatum, vervaldatum) "
            "VALUES (?,?,?,?)",
            (f"F{year}-005", "Test", "2026-01-01", "2026-01-31")
        )
        conn.commit()

    nr = next_factuurnummer(db, instellingen)
    assert nr == f"F{year}-006"
    cleanup_db(db)
