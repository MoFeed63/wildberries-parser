# Wildberries Parser (two-stage)

A scraper for the Wildberries marketplace that collects product data and exports it to SQLite in two steps.

The main idea is to read the site's own JSON responses instead of parsing HTML. Wildberries changes its markup often, but the internal API stays stable, so the parser hooks into the browser's network traffic and takes structured data directly from there.

Both stages use [Camoufox](https://camoufox.com), a hardened Firefox build with anti-detect patches, so the requests look like a real browser session.

## How it works

**Stage 1 — search results (`main.py`)**

1. Asks for a search keyword (for example `chandeliers`).
2. Opens the Wildberries search page in a headless browser.
3. Intercepts the `exactmatch` API response.
4. Takes the first 5 products, calculates the real price from the `sizes` data (price comes in kopecks, so it is divided by 100).
5. Saves article id, name, brand, price and product link to the `wb` table.

**Stage 2 — product details (`card.py`)**

1. Reads every article from the `wb` table.
2. Opens the product page for each article.
3. Intercepts the `card.json` response.
4. Extracts description, characteristics (`options`), category (`subj_name`) and package contents (`contents`).
5. Saves everything to the `details` table, linked to `wb` by article id.

Because the database sits between the two stages, you can stop after stage 1, review the data, and run stage 2 later or in batches.

## Database

```
wb
  article   INTEGER PRIMARY KEY  (UNIQUE)
  name      TEXT UNIQUE
  brand     TEXT
  price     REAL
  link      TEXT

details
  article     INTEGER PRIMARY KEY -> wb.article ON DELETE CASCADE
  name        TEXT UNIQUE
  brand       TEXT
  description TEXT
  options     TEXT   (JSON array as a string)
  subj_name   TEXT
  contents    TEXT
  price       REAL
```

`INSERT OR IGNORE` plus the `UNIQUE` constraint on article id makes repeated runs safe: duplicates are skipped, not added twice.

## Tech stack

- Python 3.11+
- Camoufox (async API) — headless browser with anti-detect patches
- Playwright-compatible page API — navigation, response interception
- SQLite3 — storage between stages

## Installation

```bash
git clone https://github.com/MoFeed63/wildberries-parser
cd wildberries-parser

pip install camoufox playwright
python -m camoufox fetch
```

`camoufox fetch` downloads the browser binary, it is required before the first run.

## Usage

Stage 1:

```bash
python main.py
# Enter search keyword: chandeliers
```

`wb.db` is created in the project folder.

Stage 2:

```bash
python card.py
```

## What can be changed for a specific task

- Number of products per query — `products[:5]` in `main.py`
- Output format — currently SQLite, easy to add CSV or Excel export
- Search by category or seller instead of a keyword
- Price history collection if the script is scheduled with cron
- Captcha handling and proxy rotation for large volumes

## Notes

- Wildberries limits request rate, so long runs are better split into batches with pauses.
- The parser is sensitive to changes in the internal API, not to page layout. If a field disappears, check the intercepted JSON first.

## License

Not specified yet.
