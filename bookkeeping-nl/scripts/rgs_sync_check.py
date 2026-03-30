"""Check consistency between RGS source artifacts and config/rgs_rules.json metadata.

Usage:
    python scripts/rgs_sync_check.py

Exit codes:
    0 = all source hashes match config metadata
    1 = one or more mismatches / missing metadata
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "rgs_rules.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def workbook_sheet_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path, "r") as zf:
        workbook_xml = zf.read("xl/workbook.xml")
    root = ET.fromstring(workbook_xml)
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    return [node.attrib.get("name", "") for node in root.findall(".//x:sheets/x:sheet", ns)]


def load_rules() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config file not found: {CONFIG_PATH}")
        return 1

    rules = load_rules()
    derived = rules.get("_meta", {}).get("derived_from", {})

    checks = [
        ("xlsx", "Def-versie RGS 3.4.xlsx"),
        ("docx_best_practice", "Best practice RGS voor de softwareleverancier 15112017.docx"),
        ("pdf_release_notes", "Toelichting releasenotes bij definitieve versie RGS 3.4.pdf"),
    ]

    has_errors = False

    print("RGS sync check")
    print("=" * 60)

    for key, _label in checks:
        item = derived.get(key, {})
        rel_path = item.get("path")
        expected_sha = item.get("sha256")

        if not rel_path:
            has_errors = True
            print(f"[MISSING] {key}: no path configured in rgs_rules.json")
            continue

        source_path = ROOT / rel_path
        if not source_path.exists():
            has_errors = True
            print(f"[MISSING] {key}: source file not found at {source_path}")
            continue

        actual_sha = sha256_file(source_path)
        if not expected_sha:
            has_errors = True
            print(f"[MISSING] {key}: no sha256 configured")
            print(f"          actual sha256 = {actual_sha}")
            continue

        if actual_sha != expected_sha:
            has_errors = True
            print(f"[MISMATCH] {key}")
            print(f"  path     : {source_path}")
            print(f"  expected : {expected_sha}")
            print(f"  actual   : {actual_sha}")
        else:
            print(f"[OK] {key}: sha256 matches")

    xlsx_meta = derived.get("xlsx", {})
    xlsx_path = ROOT / xlsx_meta.get("path", "")
    if xlsx_path.exists():
        configured = xlsx_meta.get("relevant_sheets", [])
        actual = workbook_sheet_names(xlsx_path)
        missing = [s for s in configured if s not in actual]
        if missing:
            has_errors = True
            print("[MISMATCH] xlsx relevant_sheets: configured sheet(s) not found")
            print(f"  missing  : {missing}")
            print(f"  workbook : {actual}")
        else:
            print("[OK] xlsx relevant_sheets exist in workbook")

    print("=" * 60)
    if has_errors:
        print("Result: FAIL - update config/rgs_rules.json metadata and/or source artifacts.")
        return 1

    print("Result: PASS - source artifacts and metadata are in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
