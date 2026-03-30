"""Database initialisation — reads schema.sql and applies it to the SQLite file."""
import os
import sqlite3


def init_database(db_path: str) -> None:
    schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        with open(schema_file, "r", encoding="utf-8") as fh:
            conn.executescript(fh.read())
        conn.commit()
