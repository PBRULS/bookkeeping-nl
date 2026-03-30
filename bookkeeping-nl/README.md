# Boekhouding NL

Volledig offline boekhoud­systeem voor een Nederlandse eenmanszaak met omzet onder € 10.000.

## Features

| Module | Inhoud |
|---|---|
| Verkoopfacturen | Aanmaken, verzenden, betaling bijhouden, automatisch factuurnummer |
| Inkoopfacturen | Registreren, goedkeuren, betalen |
| BTW Aangifte | Automatische berekening op basis van facturen — rubrieken 1a, 1b, 3a, 4a, 5b |
| Kasboek / Bank | Ontvangsten en uitgaven, export naar QIF (GnuCash) |
| Activa register | Lineaire en degressieve afschrijving, afschrijvingsplan |
| Voorraad | Mutaties bijhouden per artikel (inkoop/verkoop/correctie) |
| Platform kosten | Bol.com, Etsy, Amazon commissies + omgekeerde heffing |
| Relaties | Klanten & leveranciers (NL/EU/buiten EU) |
| Artikelen | Producten en diensten met BTW-tarief |
| Import/Export | CSV in/out voor alle modules, QIF export voor GnuCash |
| Audit log | SHA-256 handtekening per record — bewaarplicht 7 jaar (art. 52 AWR) |

## BTW tarieven (2026)

| Code | Tarief | Omschrijving |
|---|---|---|
| `21%` | 21% | Hoog tarief — algemeen |
| `9%` | 9% | Laag tarief — voedsel, boeken, geneesmiddelen |
| `0%` | 0% | Nultarief — export buiten EU |
| `vrij` | — | Vrijgesteld |
| `verlegd` | 0% | Omgekeerde heffing (intra-EU B2B, niet-NL platforms) |

> **Belastingregels bijwerken:** Pas alleen `config/tax_rules.json` aan — geen Python-code nodig.

## GnuCash integratie

Het kasboek kan worden geëxporteerd naar QIF-formaat:
```
GET /api/export/kasboek/qif?jaar=2026
```
In GnuCash: **Bestand → Importeren → QIF-bestand importeren...**

## Installatie

```bash
# 1. Kloon het project
git clone https://github.com/PascalBruls/bookkeeping-nl.git
cd bookkeeping-nl

# 2. Maak een virtuele omgeving aan
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Mac/Linux

# 3. Installeer afhankelijkheden
pip install -r requirements.txt

# 4. Start de applicatie
python run.py
```

Open uw browser op: **http://127.0.0.1:5000**

De SQLite-database wordt automatisch aangemaakt in `data/boekhouding.db`.

## Tests uitvoeren

```bash
pytest tests/ -v
```

## Projectstructuur

```
bookkeeping-nl/
├── run.py                      # Startpunt
├── config/
│   ├── tax_rules.json          # ← Belastingregels (hier aanpassen bij wetswijzigingen)
│   └── chart_of_accounts.json  # Vereenvoudigd RGS rekeningschema
├── backend/
│   ├── app.py                  # Flask application factory
│   ├── database/
│   │   ├── schema.sql          # Volledige database definitie
│   │   ├── init_db.py          # Database initialisatie
│   │   └── models.py           # Data access layer (repository pattern)
│   ├── routes/                 # REST API endpoints (Flask blueprints)
│   └── services/
│       ├── vat_service.py      # BTW berekeningen (leest uit tax_rules.json)
│       ├── invoice_service.py  # Factuurnummer generatie
│       ├── asset_service.py    # Activum / afschrijving berekeningen
│       └── export_service.py   # CSV + QIF export/import
├── frontend/
│   ├── index.html              # Single Page Application
│   ├── css/style.css
│   └── js/
│       ├── api.js              # Fetch wrapper
│       ├── app.js              # Router + globale helpers
│       └── pages.js            # Alle pagina-renderers
├── data/                       # SQLite database (niet in git)
├── exports/                    # Gegenereerde exports (niet in git)
└── tests/
    ├── test_vat_service.py
    └── test_invoice_service.py
```

## Juridische context

| Regel | Bron |
|---|---|
| Bewaarplicht 7 jaar | Art. 52 Algemene wet inzake rijksbelastingen (AWR) |
| BTW-aangifte kwartaal | Art. 19 Wet OB 1968 |
| KOR vrijstelling (< € 20.000) | Art. 25 Wet OB 1968 |
| Omgekeerde heffing (verlegd) | Art. 12 Wet OB 1968 |
| Intrastat drempel | € 900.000 |

> Dit systeem is **administratiehulpmiddel** en vervangt geen belastingadvies.
> Controleer uw aangifte altijd via **Mijn Belastingdienst Zakelijk**.

## Belastingregels bijwerken

Bij een wetswijziging (bijv. BTW-tarief aanpassing):

1. Open `config/tax_rules.json`
2. Pas het `rate`-veld aan van het betreffende tarief
3. Update `effective_date` en `last_updated`
4. Herstart de applicatie (`python run.py`)

Geen code-aanpassingen nodig.

## RGS broncontrole (sync check)

Controleer of de lokale RGS-bronbestanden en metadata in `config/rgs_rules.json` nog gelijk lopen:

```bash
python scripts/rgs_sync_check.py
```

Deze check vergelijkt SHA256-hashes van:
- `docs/rgs-source/Def-versie RGS 3.4.xlsx`
- `docs/rgs-source/Best practice RGS voor de softwareleverancier 15112017.docx`
- `docs/rgs-source/Toelichting releasenotes bij definitieve versie RGS 3.4.pdf`

Bij verschillen krijg je een duidelijke melding en een non-zero exit code.

## Licentie

MIT
