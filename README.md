# Terraria Search Engine

**Alejandro Costich**  
Information Retrieval — Custom Search Engine Project

---

## Domain

**Terraria Wiki** — the official wiki for Re-Logic's Terraria (2011), one of the best-selling games of all time with 64M+ copies sold. The corpus covers 30 documents across five categories: Bosses, Biomes, Weapons, Events, and Mechanics. Terraria was chosen because its rich, interlocking game systems produce natural, complex queries ("how to unlock hardmode", "best sword after plantera") that make for an interesting and realistic search engine test bed.

---

## Enhancement: G — Spell Correction

Spell correction is implemented using **Levenshtein edit distance** computed against the engine's own indexed vocabulary.

**How it works:**
1. At index build time, all unstemmed tokens from the corpus are collected into a `vocab` set (~1,600 unique terms)
2. At query time, each query token is checked against the vocab
3. If a token is not found in the vocab, the engine finds the closest matching vocab word with edit distance ≤ 2
4. A length pre-filter (`abs(len(a) - len(b)) > max_distance`) skips obviously distant words before running the full O(n×m) DP
5. If the corrected query differs from the original, the UI shows "Did you mean X?"
6. If the original query returns 0 results, the corrected query is used automatically

**Example corrections:**
- `skelton` → `skeletron`
- `plantra` → `plantera`
- `zeneth` → `zenith`

---

## Running Locally (without Docker)

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Re-scrape the corpus
python scraper.py

# 4. Run the server
uvicorn app:app --reload

# 5. Open browser
open http://localhost:8000
```

---

## Running with Docker

```bash
# Build and start
docker compose up --build

# Open browser
open http://localhost:8000

# Stop
docker compose down
```

---

## Project Structure

```
terraria-search/
├── README.md               # This file
├── corpus.json             # 30 documents from terraria.wiki.gg
├── scraper.py              # One-time wiki scraper (BeautifulSoup)
├── search_engine.py        # Text pipeline, inverted index, BM25, spell correction
├── app.py                  # FastAPI server
├── templates/
│   └── index.html          # Main search UI (Jinja2)
├── static/
│   ├── style.css           # Pixel-art dark theme
│   └── main.js             # Search logic, filters, spell suggestion UI
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Main search page |
| GET | `/search?q=moon+lord&top_k=10&category=Boss` | Search — returns JSON |
| GET | `/stats` | Index statistics |
| GET | `/index-view?term=zenith` | Posting list for a term |

---

## Screenshots

> *(Add screenshots here before submission)*

---

## Corpus Sources

All documents scraped from [terraria.wiki.gg](https://terraria.wiki.gg) — the official community wiki for Terraria, licensed under CC BY-NC-SA 3.0.