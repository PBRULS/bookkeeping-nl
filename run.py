"""
Boekhouding NL — Entry Point
Run with: python run.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.app import create_app
from backend.database.init_db import init_database

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "boekhouding.db")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "exports"), exist_ok=True)

    app = create_app(DB_PATH)
    init_database(DB_PATH)

    print("=" * 55)
    print("  Boekhouding NL — Eenmanszaak Administratiesysteem")
    print("=" * 55)
    print(f"  Database : {DB_PATH}")
    print(f"  Open in browser: http://127.0.0.1:5000")
    print("  Druk Ctrl+C om te stoppen.")
    print("=" * 55)

    app.run(debug=False, host="127.0.0.1", port=5000)
