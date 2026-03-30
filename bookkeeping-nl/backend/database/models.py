"""
Database access layer — thin repository functions.
All SQL lives here; routes and services use these functions only.
"""
import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Any


# ------------------------------------------------------------------ #
#  Connection helper                                                   #
# ------------------------------------------------------------------ #

def get_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


def rows_to_list(rows) -> list[dict]:
    return [dict(r) for r in rows]


# ------------------------------------------------------------------ #
#  Audit log                                                           #
# ------------------------------------------------------------------ #

def _sign(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def log_audit(conn: sqlite3.Connection, actie: str, tabel: str,
              record_id: int, oud: dict | None, nieuw: dict | None) -> None:
    handtekening = _sign({"tabel": tabel, "record_id": record_id,
                           "oud": oud, "nieuw": nieuw,
                           "tijdstip": datetime.utcnow().isoformat()})
    conn.execute(
        """INSERT INTO audit_log (actie, tabel, record_id, oud_waarde, nieuw_waarde, handtekening)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (actie, tabel, record_id,
         json.dumps(oud, default=str) if oud else None,
         json.dumps(nieuw, default=str) if nieuw else None,
         handtekening)
    )


# ------------------------------------------------------------------ #
#  Instellingen                                                        #
# ------------------------------------------------------------------ #

def get_all_instellingen(db_path: str) -> dict:
    with get_db(db_path) as conn:
        rows = conn.execute("SELECT sleutel, waarde FROM instellingen").fetchall()
    return {r["sleutel"]: r["waarde"] for r in rows}


def set_instelling(db_path: str, sleutel: str, waarde: str) -> None:
    with get_db(db_path) as conn:
        conn.execute(
            "INSERT INTO instellingen (sleutel, waarde) VALUES (?, ?) "
            "ON CONFLICT(sleutel) DO UPDATE SET waarde = excluded.waarde",
            (sleutel, waarde)
        )
        conn.commit()


# ------------------------------------------------------------------ #
#  Relaties                                                            #
# ------------------------------------------------------------------ #

def get_relaties(db_path: str, type_filter: str | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        if type_filter:
            rows = conn.execute(
                "SELECT * FROM relaties WHERE actief=1 AND (type=? OR type='beide') ORDER BY naam",
                (type_filter,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM relaties WHERE actief=1 ORDER BY naam"
            ).fetchall()
    return rows_to_list(rows)


def get_relatie(db_path: str, relatie_id: int) -> dict | None:
    with get_db(db_path) as conn:
        row = conn.execute("SELECT * FROM relaties WHERE id=?", (relatie_id,)).fetchone()
    return row_to_dict(row)


def create_relatie(db_path: str, data: dict) -> int:
    cols = ["type", "naam", "kvk_nummer", "btw_nummer", "eu_btw_nummer",
            "land", "locatie_type", "adres", "postcode", "plaats",
            "email", "telefoon", "iban", "notities"]
    vals = [data.get(c) for c in cols]
    with get_db(db_path) as conn:
        cur = conn.execute(
            f"INSERT INTO relaties ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
            vals
        )
        rid = cur.lastrowid
        log_audit(conn, "CREATE", "relaties", rid, None, data)
        conn.commit()
    return rid


def update_relatie(db_path: str, relatie_id: int, data: dict) -> None:
    cols = ["type", "naam", "kvk_nummer", "btw_nummer", "eu_btw_nummer",
            "land", "locatie_type", "adres", "postcode", "plaats",
            "email", "telefoon", "iban", "notities", "actief"]
    with get_db(db_path) as conn:
        old = row_to_dict(conn.execute("SELECT * FROM relaties WHERE id=?", (relatie_id,)).fetchone())
        sets = ", ".join(f"{c}=?" for c in cols)
        vals = [data.get(c, old.get(c)) for c in cols] + [relatie_id]
        conn.execute(f"UPDATE relaties SET {sets}, gewijzigd_op=datetime('now') WHERE id=?", vals)
        log_audit(conn, "UPDATE", "relaties", relatie_id, old, data)
        conn.commit()


# ------------------------------------------------------------------ #
#  Artikelen                                                           #
# ------------------------------------------------------------------ #

def get_artikelen(db_path: str) -> list[dict]:
    with get_db(db_path) as conn:
        rows = conn.execute("SELECT * FROM artikelen WHERE actief=1 ORDER BY naam").fetchall()
    return rows_to_list(rows)


def get_artikel(db_path: str, artikel_id: int) -> dict | None:
    with get_db(db_path) as conn:
        row = conn.execute("SELECT * FROM artikelen WHERE id=?", (artikel_id,)).fetchone()
    return row_to_dict(row)


def create_artikel(db_path: str, data: dict) -> int:
    cols = ["code", "naam", "omschrijving", "btw_tarief", "verkoop_prijs",
            "inkoop_prijs", "eenheid", "grootboek_omzet", "grootboek_inkoop",
            "voorraad_bijhouden", "min_voorraad"]
    vals = [data.get(c) for c in cols]
    with get_db(db_path) as conn:
        cur = conn.execute(
            f"INSERT INTO artikelen ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals
        )
        aid = cur.lastrowid
        log_audit(conn, "CREATE", "artikelen", aid, None, data)
        conn.commit()
    return aid


def update_artikel(db_path: str, artikel_id: int, data: dict) -> None:
    cols = ["code", "naam", "omschrijving", "btw_tarief", "verkoop_prijs",
            "inkoop_prijs", "eenheid", "grootboek_omzet", "grootboek_inkoop",
            "voorraad_bijhouden", "min_voorraad", "actief"]
    with get_db(db_path) as conn:
        old = row_to_dict(conn.execute("SELECT * FROM artikelen WHERE id=?", (artikel_id,)).fetchone())
        sets = ", ".join(f"{c}=?" for c in cols)
        vals = [data.get(c, old.get(c)) for c in cols] + [artikel_id]
        conn.execute(f"UPDATE artikelen SET {sets} WHERE id=?", vals)
        log_audit(conn, "UPDATE", "artikelen", artikel_id, old, data)
        conn.commit()


def get_voorraad_stand(db_path: str, artikel_id: int) -> float:
    with get_db(db_path) as conn:
        row = conn.execute(
            """SELECT COALESCE(SUM(CASE WHEN type IN ('inkoop','begin','retour','correctie') THEN aantal
                                        WHEN type='verkoop' THEN -aantal ELSE 0 END), 0) AS stand
               FROM voorraad_mutaties WHERE artikel_id=?""",
            (artikel_id,)
        ).fetchone()
    return row["stand"] if row else 0.0


# ------------------------------------------------------------------ #
#  Verkoopfacturen                                                     #
# ------------------------------------------------------------------ #

def get_verkoopfacturen(db_path: str, status: str | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM verkoopfacturen WHERE status=? ORDER BY factuurdatum DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM verkoopfacturen ORDER BY factuurdatum DESC"
            ).fetchall()
    return rows_to_list(rows)


def get_verkoopfactuur(db_path: str, factuur_id: int) -> dict | None:
    with get_db(db_path) as conn:
        factuur = row_to_dict(
            conn.execute("SELECT * FROM verkoopfacturen WHERE id=?", (factuur_id,)).fetchone()
        )
        if factuur:
            regels = rows_to_list(
                conn.execute("SELECT * FROM verkoopfactuurregels WHERE factuur_id=?", (factuur_id,)).fetchall()
            )
            factuur["regels"] = regels
    return factuur


def create_verkoopfactuur(db_path: str, header: dict, regels: list[dict]) -> int:
    cols_h = ["factuurnummer", "klant_id", "klant_naam", "klant_adres", "klant_btw_nummer",
              "factuurdatum", "vervaldatum", "status", "valuta",
              "subtotaal", "btw_21", "btw_9", "btw_0", "btw_totaal", "totaal",
              "btw_type", "omgekeerde_heffing", "betalingskenmerk", "notities"]
    vals_h = [header.get(c) for c in cols_h]

    handtekening = _sign({**header, "regels": regels})

    with get_db(db_path) as conn:
        cur = conn.execute(
            f"INSERT INTO verkoopfacturen ({','.join(cols_h)}, handtekening) "
            f"VALUES ({','.join(['?']*len(cols_h))}, ?)",
            vals_h + [handtekening]
        )
        fid = cur.lastrowid
        _insert_verkoopregels(conn, fid, regels)
        log_audit(conn, "CREATE", "verkoopfacturen", fid, None, {**header, "regels": regels})
        conn.commit()
    return fid


def _insert_verkoopregels(conn: sqlite3.Connection, fid: int, regels: list[dict]) -> None:
    cols = ["factuur_id", "artikel_id", "omschrijving", "hoeveelheid", "eenheid",
            "eenheidsprijs", "btw_tarief", "btw_bedrag", "totaal_excl", "totaal_incl",
            "grootboek_rekening"]
    for r in regels:
        vals = [fid] + [r.get(c) for c in cols[1:]]
        conn.execute(
            f"INSERT INTO verkoopfactuurregels ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
            vals
        )


def update_verkoopfactuur_status(db_path: str, factuur_id: int, status: str,
                                  betaald_bedrag: float | None = None,
                                  betalingsdatum: str | None = None) -> None:
    with get_db(db_path) as conn:
        old = row_to_dict(conn.execute("SELECT * FROM verkoopfacturen WHERE id=?", (factuur_id,)).fetchone())
        conn.execute(
            """UPDATE verkoopfacturen
               SET status=?, betaald_bedrag=COALESCE(?,betaald_bedrag),
                   betalingsdatum=COALESCE(?,betalingsdatum),
                   gewijzigd_op=datetime('now')
               WHERE id=?""",
            (status, betaald_bedrag, betalingsdatum, factuur_id)
        )
        log_audit(conn, "UPDATE_STATUS", "verkoopfacturen", factuur_id, old,
                  {"status": status, "betaald_bedrag": betaald_bedrag})
        conn.commit()


# ------------------------------------------------------------------ #
#  Inkoopfacturen                                                      #
# ------------------------------------------------------------------ #

def get_inkoopfacturen(db_path: str, status: str | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM inkoopfacturen WHERE status=? ORDER BY factuurdatum DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM inkoopfacturen ORDER BY factuurdatum DESC").fetchall()
    return rows_to_list(rows)


def get_inkoopfactuur(db_path: str, factuur_id: int) -> dict | None:
    with get_db(db_path) as conn:
        factuur = row_to_dict(
            conn.execute("SELECT * FROM inkoopfacturen WHERE id=?", (factuur_id,)).fetchone()
        )
        if factuur:
            regels = rows_to_list(
                conn.execute("SELECT * FROM inkoopfactuurregels WHERE factuur_id=?", (factuur_id,)).fetchall()
            )
            factuur["regels"] = regels
    return factuur


def create_inkoopfactuur(db_path: str, header: dict, regels: list[dict]) -> int:
    cols_h = ["referentie", "leverancier_factuur_nr", "leverancier_id", "leverancier_naam",
              "factuurdatum", "vervaldatum", "status", "valuta",
              "subtotaal", "btw_bedrag", "totaal", "categorie",
              "btw_type", "aftrekbaar_btw_pct", "notities"]
    vals_h = [header.get(c) for c in cols_h]
    handtekening = _sign({**header, "regels": regels})

    with get_db(db_path) as conn:
        cur = conn.execute(
            f"INSERT INTO inkoopfacturen ({','.join(cols_h)}, handtekening) "
            f"VALUES ({','.join(['?']*len(cols_h))}, ?)",
            vals_h + [handtekening]
        )
        fid = cur.lastrowid
        cols_r = ["factuur_id", "artikel_id", "omschrijving", "hoeveelheid",
                  "eenheidsprijs", "btw_tarief", "btw_bedrag", "totaal_excl",
                  "totaal_incl", "grootboek_rekening"]
        for r in regels:
            vals_r = [fid] + [r.get(c) for c in cols_r[1:]]
            conn.execute(
                f"INSERT INTO inkoopfactuurregels ({','.join(cols_r)}) "
                f"VALUES ({','.join(['?']*len(cols_r))})",
                vals_r
            )
        log_audit(conn, "CREATE", "inkoopfacturen", fid, None, {**header, "regels": regels})
        conn.commit()
    return fid


def update_inkoopfactuur_status(db_path: str, factuur_id: int, status: str,
                                 betaald_bedrag: float | None = None,
                                 betalingsdatum: str | None = None) -> None:
    with get_db(db_path) as conn:
        old = row_to_dict(conn.execute("SELECT * FROM inkoopfacturen WHERE id=?", (factuur_id,)).fetchone())
        conn.execute(
            """UPDATE inkoopfacturen
               SET status=?, betaald_bedrag=COALESCE(?,betaald_bedrag),
                   betalingsdatum=COALESCE(?,betalingsdatum),
                   gewijzigd_op=datetime('now')
               WHERE id=?""",
            (status, betaald_bedrag, betalingsdatum, factuur_id)
        )
        log_audit(conn, "UPDATE_STATUS", "inkoopfacturen", factuur_id, old,
                  {"status": status, "betaald_bedrag": betaald_bedrag})
        conn.commit()


# ------------------------------------------------------------------ #
#  Kasboek                                                             #
# ------------------------------------------------------------------ #

def get_kasboek(db_path: str, jaar: int | None = None,
                rekening_type: str | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        query = "SELECT * FROM kasboek WHERE 1=1"
        params: list[Any] = []
        if jaar:
            query += " AND strftime('%Y', datum) = ?"
            params.append(str(jaar))
        if rekening_type:
            query += " AND rekening_type = ?"
            params.append(rekening_type)
        query += " ORDER BY datum DESC, id DESC"
        rows = conn.execute(query, params).fetchall()
    return rows_to_list(rows)


def create_kasboek_entry(db_path: str, data: dict) -> int:
    cols = ["datum", "rekening_type", "categorie", "omschrijving", "bedrag",
            "btw_tarief", "btw_bedrag", "tegenrekening", "relatie_id",
            "factuur_id", "factuur_type", "grootboek_rekening"]
    vals = [data.get(c) for c in cols]
    handtekening = _sign(data)
    with get_db(db_path) as conn:
        cur = conn.execute(
            f"INSERT INTO kasboek ({','.join(cols)}, handtekening) "
            f"VALUES ({','.join(['?']*len(cols))}, ?)",
            vals + [handtekening]
        )
        kid = cur.lastrowid
        log_audit(conn, "CREATE", "kasboek", kid, None, data)
        conn.commit()
    return kid


# ------------------------------------------------------------------ #
#  Activa                                                              #
# ------------------------------------------------------------------ #

def get_activa(db_path: str) -> list[dict]:
    with get_db(db_path) as conn:
        rows = conn.execute("SELECT * FROM activa WHERE actief=1 ORDER BY aanschafdatum DESC").fetchall()
    return rows_to_list(rows)


def get_actief(db_path: str, actief_id: int) -> dict | None:
    with get_db(db_path) as conn:
        row = conn.execute("SELECT * FROM activa WHERE id=?", (actief_id,)).fetchone()
        item = row_to_dict(row)
        if item:
            afschr = rows_to_list(
                conn.execute("SELECT * FROM afschrijvingen WHERE actief_id=? ORDER BY datum", (actief_id,)).fetchall()
            )
            item["afschrijvingen"] = afschr
    return item


def create_actief(db_path: str, data: dict) -> int:
    cols = ["naam", "omschrijving", "categorie", "aanschafdatum", "aanschafwaarde",
            "restwaarde", "afschrijvingsjaren", "afschrijvingsmethode",
            "leverancier_id", "inkoop_factuur_id", "grootboek_rekening"]
    vals = [data.get(c) for c in cols]
    with get_db(db_path) as conn:
        cur = conn.execute(
            f"INSERT INTO activa ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals
        )
        aid = cur.lastrowid
        log_audit(conn, "CREATE", "activa", aid, None, data)
        conn.commit()
    return aid


def create_afschrijving(db_path: str, data: dict) -> int:
    with get_db(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO afschrijvingen (actief_id, datum, bedrag, boekwaarde_na, periode) VALUES (?,?,?,?,?)",
            (data["actief_id"], data["datum"], data["bedrag"], data["boekwaarde_na"], data["periode"])
        )
        aid = cur.lastrowid
        log_audit(conn, "CREATE", "afschrijvingen", aid, None, data)
        conn.commit()
    return aid


# ------------------------------------------------------------------ #
#  Platform kosten                                                     #
# ------------------------------------------------------------------ #

def get_platform_kosten(db_path: str, jaar: int | None = None) -> list[dict]:
    with get_db(db_path) as conn:
        if jaar:
            rows = conn.execute(
                "SELECT * FROM platform_kosten WHERE strftime('%Y', datum)=? ORDER BY datum DESC",
                (str(jaar),)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM platform_kosten ORDER BY datum DESC").fetchall()
    return rows_to_list(rows)


def create_platform_kost(db_path: str, data: dict) -> int:
    cols = ["datum", "platform", "type", "omschrijving", "bedrag_excl_btw",
            "btw_bedrag", "btw_tarief", "totaal", "omgekeerde_heffing",
            "factuur_referentie", "grootboek_rekening"]
    vals = [data.get(c) for c in cols]
    with get_db(db_path) as conn:
        cur = conn.execute(
            f"INSERT INTO platform_kosten ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals
        )
        pid = cur.lastrowid
        log_audit(conn, "CREATE", "platform_kosten", pid, None, data)
        conn.commit()
    return pid


# ------------------------------------------------------------------ #
#  BTW periodes                                                        #
# ------------------------------------------------------------------ #

def get_btw_periodes(db_path: str) -> list[dict]:
    with get_db(db_path) as conn:
        rows = conn.execute("SELECT * FROM btw_periodes ORDER BY startdatum DESC").fetchall()
    return rows_to_list(rows)


def upsert_btw_periode(db_path: str, data: dict) -> None:
    with get_db(db_path) as conn:
        conn.execute(
            """INSERT INTO btw_periodes
               (periode, type, startdatum, einddatum, status,
                omzet_21, btw_21_af, omzet_9, btw_9_af,
                omzet_0, omzet_verlegd, btw_verlegd_af,
                omzet_eu_b2c, btw_eu_b2c_af,
                voorbelasting_totaal, saldo_btw)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(periode) DO UPDATE SET
                   status=excluded.status,
                   omzet_21=excluded.omzet_21,
                   btw_21_af=excluded.btw_21_af,
                   omzet_9=excluded.omzet_9,
                   btw_9_af=excluded.btw_9_af,
                   omzet_0=excluded.omzet_0,
                   omzet_verlegd=excluded.omzet_verlegd,
                   btw_verlegd_af=excluded.btw_verlegd_af,
                   omzet_eu_b2c=excluded.omzet_eu_b2c,
                   btw_eu_b2c_af=excluded.btw_eu_b2c_af,
                   voorbelasting_totaal=excluded.voorbelasting_totaal,
                   saldo_btw=excluded.saldo_btw""",
            (data["periode"], data["type"], data["startdatum"], data["einddatum"],
             data.get("status", "concept"),
             data.get("omzet_21", 0), data.get("btw_21_af", 0),
             data.get("omzet_9", 0), data.get("btw_9_af", 0),
             data.get("omzet_0", 0), data.get("omzet_verlegd", 0),
             data.get("btw_verlegd_af", 0),
             data.get("omzet_eu_b2c", 0), data.get("btw_eu_b2c_af", 0),
             data.get("voorbelasting_totaal", 0), data.get("saldo_btw", 0))
        )
        conn.commit()


# ------------------------------------------------------------------ #
#  Dashboard totals                                                    #
# ------------------------------------------------------------------ #

def get_dashboard_stats(db_path: str, jaar: int) -> dict:
    jaar_str = str(jaar)
    with get_db(db_path) as conn:
        omzet = conn.execute(
            "SELECT COALESCE(SUM(subtotaal),0) AS v FROM verkoopfacturen "
            "WHERE strftime('%Y',factuurdatum)=? AND status != 'gecrediteerd'", (jaar_str,)
        ).fetchone()["v"]

        inkoop = conn.execute(
            "SELECT COALESCE(SUM(subtotaal),0) AS v FROM inkoopfacturen "
            "WHERE strftime('%Y',factuurdatum)=? AND status != 'gecrediteerd'", (jaar_str,)
        ).fetchone()["v"]

        openstaand = conn.execute(
            "SELECT COALESCE(SUM(totaal - betaald_bedrag),0) AS v FROM verkoopfacturen "
            "WHERE strftime('%Y',factuurdatum)=? AND status IN ('verzonden','deels_betaald')",
            (jaar_str,)
        ).fetchone()["v"]

        te_betalen = conn.execute(
            "SELECT COALESCE(SUM(totaal - betaald_bedrag),0) AS v FROM inkoopfacturen "
            "WHERE strftime('%Y',factuurdatum)=? AND status IN ('ontvangen','goedgekeurd','deels_betaald')",
            (jaar_str,)
        ).fetchone()["v"]

        btw_af = conn.execute(
            "SELECT COALESCE(SUM(btw_totaal),0) AS v FROM verkoopfacturen "
            "WHERE strftime('%Y',factuurdatum)=? AND status != 'gecrediteerd'", (jaar_str,)
        ).fetchone()["v"]

        btw_voor = conn.execute(
            "SELECT COALESCE(SUM(btw_bedrag),0) AS v FROM inkoopfacturen "
            "WHERE strftime('%Y',factuurdatum)=? AND status != 'gecrediteerd'", (jaar_str,)
        ).fetchone()["v"]

    return {
        "jaar": jaar,
        "omzet_excl_btw": round(omzet, 2),
        "inkoop_excl_btw": round(inkoop, 2),
        "bruto_winst": round(omzet - inkoop, 2),
        "openstaande_debiteuren": round(openstaand, 2),
        "openstaande_crediteuren": round(te_betalen, 2),
        "btw_af_te_dragen": round(btw_af, 2),
        "btw_voorbelasting": round(btw_voor, 2),
        "btw_saldo": round(btw_af - btw_voor, 2),
    }
