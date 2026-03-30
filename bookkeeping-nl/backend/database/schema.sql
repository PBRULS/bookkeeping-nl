-- =============================================================
-- Boekhouding NL — SQLite Database Schema
-- Standaard: vereenvoudigd RGS voor eenmanszaak < €10.000 omzet
-- =============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- --------------------------------------------------------
-- Relaties (klanten en leveranciers)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS relaties (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    type              TEXT NOT NULL CHECK(type IN ('klant', 'leverancier', 'beide')),
    naam              TEXT NOT NULL,
    kvk_nummer        TEXT,
    btw_nummer        TEXT,
    eu_btw_nummer     TEXT,
    land              TEXT NOT NULL DEFAULT 'NL',
    locatie_type      TEXT NOT NULL DEFAULT 'NL'
                      CHECK(locatie_type IN ('NL', 'EU', 'buiten_EU')),
    adres             TEXT,
    postcode          TEXT,
    plaats            TEXT,
    email             TEXT,
    telefoon          TEXT,
    iban              TEXT,
    notities          TEXT,
    actief            INTEGER NOT NULL DEFAULT 1,
    aangemaakt_op     TEXT NOT NULL DEFAULT (datetime('now')),
    gewijzigd_op      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- Artikelen (producten en diensten)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS artikelen (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    code              TEXT UNIQUE,
    naam              TEXT NOT NULL,
    omschrijving      TEXT,
    btw_tarief        TEXT NOT NULL DEFAULT '21%'
                      CHECK(btw_tarief IN ('21%', '9%', '0%', 'vrij', 'verlegd')),
    verkoop_prijs     REAL,
    inkoop_prijs      REAL,
    eenheid           TEXT NOT NULL DEFAULT 'stuk',
    grootboek_omzet   TEXT NOT NULL DEFAULT '4000',
    grootboek_inkoop  TEXT NOT NULL DEFAULT '5000',
    voorraad_bijhouden INTEGER NOT NULL DEFAULT 0,
    min_voorraad      REAL NOT NULL DEFAULT 0,
    actief            INTEGER NOT NULL DEFAULT 1,
    aangemaakt_op     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- Voorraad mutaties
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS voorraad_mutaties (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    artikel_id        INTEGER NOT NULL REFERENCES artikelen(id),
    datum             TEXT NOT NULL,
    type              TEXT NOT NULL
                      CHECK(type IN ('inkoop', 'verkoop', 'correctie', 'retour', 'begin')),
    factuur_id        INTEGER,
    factuur_type      TEXT CHECK(factuur_type IN ('verkoop', 'inkoop')),
    aantal            REAL NOT NULL,
    eenheidsprijs     REAL,
    omschrijving      TEXT,
    aangemaakt_op     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- Verkoopfacturen
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS verkoopfacturen (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    factuurnummer      TEXT UNIQUE NOT NULL,
    klant_id           INTEGER REFERENCES relaties(id),
    klant_naam         TEXT NOT NULL,
    klant_adres        TEXT,
    klant_btw_nummer   TEXT,
    factuurdatum       TEXT NOT NULL,
    vervaldatum        TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'concept'
                       CHECK(status IN ('concept','verzonden','betaald','deels_betaald','verlopen','gecrediteerd')),
    valuta             TEXT NOT NULL DEFAULT 'EUR',
    subtotaal          REAL NOT NULL DEFAULT 0,
    btw_21             REAL NOT NULL DEFAULT 0,
    btw_9              REAL NOT NULL DEFAULT 0,
    btw_0              REAL NOT NULL DEFAULT 0,
    btw_totaal         REAL NOT NULL DEFAULT 0,
    totaal             REAL NOT NULL DEFAULT 0,
    betaald_bedrag     REAL NOT NULL DEFAULT 0,
    betalingsdatum     TEXT,
    betalingskenmerk   TEXT,
    btw_type           TEXT NOT NULL DEFAULT 'NL'
                       CHECK(btw_type IN ('NL','EU_B2B','EU_B2C','export')),
    omgekeerde_heffing INTEGER NOT NULL DEFAULT 0,
    notities           TEXT,
    handtekening       TEXT,
    aangemaakt_op      TEXT NOT NULL DEFAULT (datetime('now')),
    gewijzigd_op       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- Verkoopfactuurregels
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS verkoopfactuurregels (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    factuur_id        INTEGER NOT NULL REFERENCES verkoopfacturen(id) ON DELETE CASCADE,
    artikel_id        INTEGER REFERENCES artikelen(id),
    omschrijving      TEXT NOT NULL,
    hoeveelheid       REAL NOT NULL DEFAULT 1,
    eenheid           TEXT NOT NULL DEFAULT 'stuk',
    eenheidsprijs     REAL NOT NULL,
    btw_tarief        TEXT NOT NULL DEFAULT '21%',
    btw_bedrag        REAL NOT NULL DEFAULT 0,
    totaal_excl       REAL NOT NULL DEFAULT 0,
    totaal_incl       REAL NOT NULL DEFAULT 0,
    grootboek_rekening TEXT NOT NULL DEFAULT '4000'
);

-- --------------------------------------------------------
-- Inkoopfacturen
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS inkoopfacturen (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    referentie             TEXT,
    leverancier_factuur_nr TEXT,
    leverancier_id         INTEGER REFERENCES relaties(id),
    leverancier_naam       TEXT NOT NULL,
    factuurdatum           TEXT NOT NULL,
    vervaldatum            TEXT NOT NULL,
    status                 TEXT NOT NULL DEFAULT 'ontvangen'
                           CHECK(status IN ('ontvangen','goedgekeurd','betaald','deels_betaald','gecrediteerd')),
    valuta                 TEXT NOT NULL DEFAULT 'EUR',
    subtotaal              REAL NOT NULL DEFAULT 0,
    btw_bedrag             REAL NOT NULL DEFAULT 0,
    totaal                 REAL NOT NULL DEFAULT 0,
    betaald_bedrag         REAL NOT NULL DEFAULT 0,
    betalingsdatum         TEXT,
    categorie              TEXT,
    btw_type               TEXT NOT NULL DEFAULT 'NL'
                           CHECK(btw_type IN ('NL','EU_B2B','EU_B2C','import')),
    aftrekbaar_btw_pct     REAL NOT NULL DEFAULT 100,
    notities               TEXT,
    handtekening           TEXT,
    aangemaakt_op          TEXT NOT NULL DEFAULT (datetime('now')),
    gewijzigd_op           TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- Inkoopfactuurregels
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS inkoopfactuurregels (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    factuur_id        INTEGER NOT NULL REFERENCES inkoopfacturen(id) ON DELETE CASCADE,
    artikel_id        INTEGER REFERENCES artikelen(id),
    omschrijving      TEXT NOT NULL,
    hoeveelheid       REAL NOT NULL DEFAULT 1,
    eenheidsprijs     REAL NOT NULL,
    btw_tarief        TEXT NOT NULL DEFAULT '21%',
    btw_bedrag        REAL NOT NULL DEFAULT 0,
    totaal_excl       REAL NOT NULL DEFAULT 0,
    totaal_incl       REAL NOT NULL DEFAULT 0,
    grootboek_rekening TEXT NOT NULL DEFAULT '5000'
);

-- --------------------------------------------------------
-- Activa register (vaste activa)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS activa (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    naam                  TEXT NOT NULL,
    omschrijving          TEXT,
    categorie             TEXT,
    aanschafdatum         TEXT NOT NULL,
    aanschafwaarde        REAL NOT NULL,
    restwaarde            REAL NOT NULL DEFAULT 0,
    afschrijvingsjaren    INTEGER NOT NULL DEFAULT 5,
    afschrijvingsmethode  TEXT NOT NULL DEFAULT 'lineair'
                          CHECK(afschrijvingsmethode IN ('lineair', 'degressief')),
    leverancier_id        INTEGER REFERENCES relaties(id),
    inkoop_factuur_id     INTEGER REFERENCES inkoopfacturen(id),
    grootboek_rekening    TEXT NOT NULL DEFAULT '0200',
    actief                INTEGER NOT NULL DEFAULT 1,
    vervreemding_datum    TEXT,
    vervreemding_waarde   REAL,
    aangemaakt_op         TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- Afschrijvingen
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS afschrijvingen (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    actief_id        INTEGER NOT NULL REFERENCES activa(id),
    datum            TEXT NOT NULL,
    bedrag           REAL NOT NULL,
    boekwaarde_na    REAL NOT NULL,
    periode          TEXT NOT NULL,
    aangemaakt_op    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- Kasboek / bankboek
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS kasboek (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    datum             TEXT NOT NULL,
    rekening_type     TEXT NOT NULL DEFAULT 'bank'
                      CHECK(rekening_type IN ('kas','bank','pin')),
    categorie         TEXT NOT NULL
                      CHECK(categorie IN ('ontvangst','uitgave')),
    omschrijving      TEXT NOT NULL,
    bedrag            REAL NOT NULL,
    btw_tarief        TEXT NOT NULL DEFAULT '0%',
    btw_bedrag        REAL NOT NULL DEFAULT 0,
    tegenrekening     TEXT,
    relatie_id        INTEGER REFERENCES relaties(id),
    factuur_id        INTEGER,
    factuur_type      TEXT CHECK(factuur_type IN ('verkoop','inkoop')),
    grootboek_rekening TEXT,
    saldo_na          REAL,
    handtekening      TEXT,
    aangemaakt_op     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- Platform kosten (Bol.com, Etsy, Amazon, etc.)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS platform_kosten (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    datum               TEXT NOT NULL,
    platform            TEXT NOT NULL,
    type                TEXT NOT NULL
                        CHECK(type IN ('commissie','abonnement','verzendkosten','reclame','overig')),
    omschrijving        TEXT,
    bedrag_excl_btw     REAL NOT NULL,
    btw_bedrag          REAL NOT NULL DEFAULT 0,
    btw_tarief          TEXT NOT NULL DEFAULT '21%',
    totaal              REAL NOT NULL,
    omgekeerde_heffing  INTEGER NOT NULL DEFAULT 0,
    factuur_referentie  TEXT,
    grootboek_rekening  TEXT NOT NULL DEFAULT '7000',
    aangemaakt_op       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- BTW periodes / aangiften
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS btw_periodes (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    periode               TEXT UNIQUE NOT NULL,
    type                  TEXT NOT NULL CHECK(type IN ('kwartaal','maand','jaar')),
    startdatum            TEXT NOT NULL,
    einddatum             TEXT NOT NULL,
    status                TEXT NOT NULL DEFAULT 'open'
                          CHECK(status IN ('open','concept','ingediend','betaald')),
    omzet_21              REAL NOT NULL DEFAULT 0,
    btw_21_af             REAL NOT NULL DEFAULT 0,
    omzet_9               REAL NOT NULL DEFAULT 0,
    btw_9_af              REAL NOT NULL DEFAULT 0,
    omzet_0               REAL NOT NULL DEFAULT 0,
    omzet_verlegd         REAL NOT NULL DEFAULT 0,
    btw_verlegd_af        REAL NOT NULL DEFAULT 0,
    omzet_eu_b2c          REAL NOT NULL DEFAULT 0,
    btw_eu_b2c_af         REAL NOT NULL DEFAULT 0,
    voorbelasting_totaal  REAL NOT NULL DEFAULT 0,
    saldo_btw             REAL NOT NULL DEFAULT 0,
    ingediend_op          TEXT,
    betaald_op            TEXT,
    aangemaakt_op         TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- Grootboek mutaties (dubbel boekhouden)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS grootboek_mutaties (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    datum            TEXT NOT NULL,
    periode          TEXT NOT NULL,
    omschrijving     TEXT NOT NULL,
    debet_rekening   TEXT NOT NULL,
    credit_rekening  TEXT NOT NULL,
    bedrag           REAL NOT NULL,
    bron_type        TEXT,
    bron_id          INTEGER,
    aangemaakt_op    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- --------------------------------------------------------
-- Audit log (exportbestendig / bewaarplicht 7 jaar)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tijdstip      TEXT NOT NULL DEFAULT (datetime('now')),
    gebruiker     TEXT NOT NULL DEFAULT 'system',
    actie         TEXT NOT NULL,
    tabel         TEXT,
    record_id     INTEGER,
    oud_waarde    TEXT,
    nieuw_waarde  TEXT,
    handtekening  TEXT
);

-- --------------------------------------------------------
-- Instellingen (applicatie-instellingen)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS instellingen (
    sleutel   TEXT PRIMARY KEY,
    waarde    TEXT NOT NULL,
    omschrijving TEXT
);

-- Standaard instellingen
INSERT OR IGNORE INTO instellingen (sleutel, waarde, omschrijving) VALUES
    ('bedrijfsnaam',      '',           'Naam van de eenmanszaak'),
    ('kvk_nummer',        '',           'KvK-nummer'),
    ('btw_nummer',        '',           'BTW-nummer (OB-nummer)'),
    ('iban',              '',           'IBAN-bankrekeningnummer'),
    ('adres',             '',           'Bezoekadres'),
    ('postcode',          '',           'Postcode'),
    ('plaats',            '',           'Vestigingsplaats'),
    ('email',             '',           'E-mailadres'),
    ('telefoon',          '',           'Telefoonnummer'),
    ('website',           '',           'Website'),
    ('factuur_prefix',    'F',          'Prefix voor factuurnummers (bijv. F2026-)'),
    ('factuur_startnum',  '1',          'Startnummer voor factuurreeks'),
    ('btw_periode',       'kwartaal',   'Aangifteperiode: kwartaal, maand of jaar'),
    ('kor_actief',        'false',      'Kleine Ondernemersregeling actief (true/false)'),
    ('betalingstermijn',  '30',         'Standaard betalingstermijn in dagen'),
    ('factuur_voettekst', 'Bedankt voor uw bestelling.', 'Voettekst op facturen');
