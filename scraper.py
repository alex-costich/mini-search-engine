"""
scraper.py — Terraria Wiki corpus builder
Scrapes HTML from terraria.wiki.gg (MediaWiki extract API not supported).
Run once: python scraper.py
Outputs: corpus.json
"""

import requests
import json
import time
import re
from typing import Optional
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://terraria.wiki.gg/wiki/"

TARGET_PAGES = [
    # Bosses
    "Eye_of_Cthulhu", "Eater_of_Worlds", "Brain_of_Cthulhu", "Skeletron",
    "Wall_of_Flesh", "The_Twins", "The_Destroyer", "Skeletron_Prime",
    "Plantera", "Golem", "Duke_Fishron", "Moon_Lord", "Queen_Bee",
    # Biomes
    "The_Corruption", "The_Crimson", "The_Hallow", "Underground_Jungle",
    "Desert", "Tundra", "Ocean",
    # Weapons / Items
    "Zenith", "Terra_Blade", "Meowmere", "Megashark", "Last_Prism",
    "Copper_Shortsword",
    # Mechanics / Events
    "Hardmode", "Blood_Moon", "Solar_Eclipse", "Goblin_Army",
    "Journey_Mode", "Terraria",
]

CATEGORY_MAP = {
    "Eye_of_Cthulhu": "Boss", "Eater_of_Worlds": "Boss", "Brain_of_Cthulhu": "Boss",
    "Skeletron": "Boss", "Wall_of_Flesh": "Boss", "The_Twins": "Boss",
    "The_Destroyer": "Boss", "Skeletron_Prime": "Boss", "Plantera": "Boss",
    "Golem": "Boss", "Duke_Fishron": "Boss", "Moon_Lord": "Boss", "Queen_Bee": "Boss",
    "The_Corruption": "Biome", "The_Crimson": "Biome", "The_Hallow": "Biome",
    "Underground_Jungle": "Biome", "Desert": "Biome", "Tundra": "Biome", "Ocean": "Biome",
    "Zenith": "Weapon", "Terra_Blade": "Weapon", "Meowmere": "Weapon",
    "Megashark": "Weapon", "Last_Prism": "Weapon", "Copper_Shortsword": "Weapon",
    "Hardmode": "Mechanic", "Journey_Mode": "Mechanic", "Terraria": "Mechanic",
    "Blood_Moon": "Event", "Solar_Eclipse": "Event", "Goblin_Army": "Event",
}


def fetch_page(slug: str) -> Optional[dict]:
    url = BASE_URL + slug
    try:
        resp = requests.get(url, timeout=15, verify=False, headers={
            "User-Agent": "Mozilla/5.0 (educational project scraper)"
        })
        resp.raise_for_status()
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Page title
    title_tag = soup.find("h1", {"id": "firstHeading"})
    title = title_tag.get_text(strip=True) if title_tag else slug.replace("_", " ")

    # Main content div
    content_div = soup.find("div", {"id": "mw-content-text"})
    if not content_div:
        print(f"  [SKIP] No content div found")
        return None

    # Remove unwanted elements: tables, navboxes, infoboxes, TOC, references
    for tag in content_div.find_all(["table", "sup", "div"], class_=re.compile(
        r"navbox|infobox|toc|reflist|mw-references|noprint"
    )):
        tag.decompose()
    for tag in content_div.find_all("div", {"id": re.compile(r"toc")}):
        tag.decompose()

    # Extract paragraphs only
    paragraphs = content_div.find_all("p")
    text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)

    # Clean up whitespace and citations like [1]
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    words = text.split()
    if len(words) < 50:
        print(f"  [SKIP] Too short ({len(words)} words)")
        return None

    trimmed = " ".join(words[:800])

    return {
        "id": slug.lower(),
        "title": title,
        "text": trimmed,
        "url": url,
        "category": CATEGORY_MAP.get(slug, "General"),
        "word_count": min(len(words), 800),
    }


def main():
    corpus = []
    print(f"Scraping {len(TARGET_PAGES)} pages from Terraria Wiki...\n")

    for i, slug in enumerate(TARGET_PAGES, 1):
        print(f"[{i:02d}/{len(TARGET_PAGES)}] {slug.replace('_', ' ')}")
        doc = fetch_page(slug)
        if doc:
            corpus.append(doc)
            print(f"  OK — {doc['word_count']} words [{doc['category']}]")
        time.sleep(1.5)  # polite delay, avoids 429

    print(f"\nDone. {len(corpus)} documents collected.")

    with open("corpus.json", "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)

    print("Saved to corpus.json")

    if corpus:
        total_words = sum(d["word_count"] for d in corpus)
        print(f"\nCorpus stats:")
        print(f"  Documents    : {len(corpus)}")
        print(f"  Total words  : {total_words:,}")
        print(f"  Avg words/doc: {total_words // len(corpus)}")
        cats = {}
        for d in corpus:
            cats[d["category"]] = cats.get(d["category"], 0) + 1
        for cat, count in sorted(cats.items()):
            print(f"  {cat}: {count} docs")
    else:
        print("\nNo documents collected — check your network/Zscaler.")


if __name__ == "__main__":
    main()