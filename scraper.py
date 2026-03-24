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

PAGES = [

    # Bosses
    "Eye_of_Cthulhu", "Eater_of_Worlds", "Brain_of_Cthulhu", "Skeletron",
    "Wall_of_Flesh", "The_Twins", "The_Destroyer", "Skeletron_Prime",
    "Plantera", "Golem", "Duke_Fishron", "Moon_Lord", "Queen_Bee",
    "King_Slime", "Deerclops", "Queen_Slime", "Empress_of_Light",
    "Lunatic_Cultist", "Dark_Mage", "Ogre", "Betsy",
    "Flying_Dutchman", "Mourning_Wood", "Pumpking", "Ice_Queen",
    "Santa-NK1", "Everscream",

    # Biomes
    "The_Corruption", "The_Crimson", "The_Hallow", "Underground_Jungle",
    "Desert", "Tundra", "Ocean", "Underground", "Cavern",
    "The_Underworld", "Space", "Dungeon", "Jungle",
    "Mushroom_biome", "Granite_Cave", "Marble_Cave",

    # Weapons
    "Zenith", "Terra_Blade", "Meowmere", "Megashark", "Last_Prism",
    "Copper_Shortsword", "Night's_Edge", "Excalibur", "True_Excalibur",
    "True_Night's_Edge", "Death_Sickle", "Vampire_Knives",
    "Scourge_of_the_Corruptor", "Piranha_Gun", "Snowball_Cannon",
    "Flamethrower", "Clockwork_Assault_Rifle", "Uzi", "Chain_Gun",
    "Golden_Shower", "Crystal_Storm", "Blizzard_Staff",
    "Razorblade_Typhoon", "Bubble_Gun", "Nimbus_Rod",
    "Bat_Scepter", "Terraprisma", "Phantasm",
    "Influx_Waver", "Star_Wrath", "Tsunami",

    # Armor
    "Molten_armor", "Meteor_armor", "Jungle_armor",
    "Hallowed_armor", "Chlorophyte_armor", "Turtle_armor",
    "Beetle_armor", "Shroomite_armor", "Spectre_armor",
    "Solar_Flare_armor", "Nebula_armor", "Vortex_armor",
    "Stardust_armor",

    # NPCs
    "Guide", "Merchant", "Nurse", "Arms_Dealer", "Dryad",
    "Demolitionist", "Goblin_Tinkerer", "Wizard", "Mechanic",
    "Clothier", "Tax_Collector", "Tavernkeep", "Painter",
    "Witch_Doctor", "Pirate", "Stylist", "Angler", "Party_Girl",
    "Truffle", "Steampunker", "Cyborg", "Santa_Claus",
    "Princess", "Zoologist",

    # Events
    "Blood_Moon", "Solar_Eclipse", "Goblin_Army",
    "Martian_Madness", "Pumpkin_Moon", "Frost_Moon",
    "Old_One%27s_Army", "Pirate_Invasion", "Frost_Legion",

    # Mechanics
    "Hardmode", "Journey_Mode", "Terraria",
    "Crafting", "Fishing", "Mining", "Building",
    "NPC_happiness", "Buffs", "Debuffs", "Luck",
    "Torch_God", "Bestiary",

    # Accessories
    "Ankh_Shield", "Celestial_Shell", "Papyrus_Scarab",
    "Destroyer_Emblem", "Avenger_Emblem", "Mechanical_Glove",
    "Fire_Gauntlet", "Yoyo_Bag", "Master_Ninja_Gear",
    "Frozen_Turtle_Shell",
]

CATEGORY_MAP = {
    # Original bosses
    "Eye_of_Cthulhu": "Boss", "Eater_of_Worlds": "Boss", "Brain_of_Cthulhu": "Boss",
    "Skeletron": "Boss", "Wall_of_Flesh": "Boss", "The_Twins": "Boss",
    "The_Destroyer": "Boss", "Skeletron_Prime": "Boss", "Plantera": "Boss",
    "Golem": "Boss", "Duke_Fishron": "Boss", "Moon_Lord": "Boss", "Queen_Bee": "Boss",
    # New bosses
    "King_Slime": "Boss", "Deerclops": "Boss", "Queen_Slime": "Boss",
    "Empress_of_Light": "Boss", "Lunatic_Cultist": "Boss", "Dark_Mage": "Boss",
    "Ogre": "Boss", "Betsy": "Boss", "Flying_Dutchman": "Boss",
    "Mourning_Wood": "Boss", "Pumpking": "Boss", "Ice_Queen": "Boss",
    "Santa-NK1": "Boss", "Everscream": "Boss",
    # Biomes
    "The_Corruption": "Biome", "The_Crimson": "Biome", "The_Hallow": "Biome",
    "Underground_Jungle": "Biome", "Desert": "Biome", "Tundra": "Biome", "Ocean": "Biome",
    "Underground": "Biome", "Cavern": "Biome", "The_Underworld": "Biome",
    "Space": "Biome", "Dungeon": "Biome", "Jungle": "Biome",
    "Mushroom_biome": "Biome", "Granite_Cave": "Biome", "Marble_Cave": "Biome",
    # Weapons
    "Zenith": "Weapon", "Terra_Blade": "Weapon", "Meowmere": "Weapon",
    "Megashark": "Weapon", "Last_Prism": "Weapon", "Copper_Shortsword": "Weapon",
    "Night's_Edge": "Weapon", "Excalibur": "Weapon", "True_Excalibur": "Weapon",
    "True_Night's_Edge": "Weapon", "Death_Sickle": "Weapon",
    "Vampire_Knives": "Weapon", "Scourge_of_the_Corruptor": "Weapon",
    "Piranha_Gun": "Weapon", "Snowball_Cannon": "Weapon", "Flamethrower": "Weapon",
    "Clockwork_Assault_Rifle": "Weapon", "Uzi": "Weapon", "Chain_Gun": "Weapon",
    "Golden_Shower": "Weapon", "Crystal_Storm": "Weapon", "Blizzard_Staff": "Weapon",
    "Razorblade_Typhoon": "Weapon", "Bubble_Gun": "Weapon", "Nimbus_Rod": "Weapon",
    "Bat_Scepter": "Weapon", "Terraprisma": "Weapon", "Phantasm": "Weapon",
    "Influx_Waver": "Weapon", "Star_Wrath": "Weapon", "Tsunami": "Weapon",
    # Armor
    "Molten_armor": "Armor", "Meteor_armor": "Armor", "Jungle_armor": "Armor",
    "Hallowed_armor": "Armor", "Chlorophyte_armor": "Armor", "Turtle_armor": "Armor",
    "Beetle_armor": "Armor", "Shroomite_armor": "Armor", "Spectre_armor": "Armor",
    "Solar_Flare_armor": "Armor", "Nebula_armor": "Armor", "Vortex_armor": "Armor",
    "Stardust_armor": "Armor",
    # NPCs
    "Guide": "NPC", "Merchant": "NPC", "Nurse": "NPC", "Arms_Dealer": "NPC",
    "Dryad": "NPC", "Demolitionist": "NPC", "Goblin_Tinkerer": "NPC",
    "Wizard": "NPC", "Mechanic": "NPC", "Clothier": "NPC", "Tax_Collector": "NPC",
    "Tavernkeep": "NPC", "Painter": "NPC", "Witch_Doctor": "NPC", "Pirate": "NPC",
    "Stylist": "NPC", "Angler": "NPC", "Party_Girl": "NPC", "Truffle": "NPC",
    "Steampunker": "NPC", "Cyborg": "NPC", "Santa_Claus": "NPC",
    "Princess": "NPC", "Zoologist": "NPC",
    # Events
    "Blood_Moon": "Event", "Solar_Eclipse": "Event", "Goblin_Army": "Event",
    "Martian_Madness": "Event", "Pumpkin_Moon": "Event", "Frost_Moon": "Event",
    "Old_One%27s_Army": "Event", "Pirate_Invasion": "Event", "Frost_Legion": "Event",
    # Mechanics
    "Hardmode": "Mechanic", "Journey_Mode": "Mechanic", "Terraria": "Mechanic",
    "Crafting": "Mechanic", "Fishing": "Mechanic", "Mining": "Mechanic",
    "Building": "Mechanic", "NPC_happiness": "Mechanic", "Buffs": "Mechanic",
    "Debuffs": "Mechanic", "Luck": "Mechanic", "Torch_God": "Mechanic",
    "Bestiary": "Mechanic",
    # Accessories
    "Ankh_Shield": "Accessory", "Celestial_Shell": "Accessory",
    "Papyrus_Scarab": "Accessory", "Destroyer_Emblem": "Accessory",
    "Avenger_Emblem": "Accessory", "Mechanical_Glove": "Accessory",
    "Fire_Gauntlet": "Accessory", "Yoyo_Bag": "Accessory",
    "Master_Ninja_Gear": "Accessory", "Frozen_Turtle_Shell": "Accessory",
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

    title_tag = soup.find("h1", {"id": "firstHeading"})
    title = title_tag.get_text(strip=True) if title_tag else slug.replace("_", " ")

    content_div = soup.find("div", {"id": "mw-content-text"})
    if not content_div:
        print(f"  [SKIP] No content div found")
        return None

    for tag in content_div.find_all(["table", "sup", "div"], class_=re.compile(
        r"navbox|infobox|toc|reflist|mw-references|noprint"
    )):
        tag.decompose()
    for tag in content_div.find_all("div", {"id": re.compile(r"toc")}):
        tag.decompose()

    paragraphs = content_div.find_all("p")
    text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    words = text.split()
    if len(words) < 50:
        print(f"  [SKIP] Too short ({len(words)} words)")
        return None

    trimmed = " ".join(words[:800])

    return {
        "id": slug.lower().replace("%27", "").replace("'", ""),
        "title": title,
        "text": trimmed,
        "url": url,
        "category": CATEGORY_MAP.get(slug, "General"),
        "word_count": min(len(words), 800),
    }


def main():
    try:
        with open("corpus.json", "r", encoding="utf-8") as f:
            corpus = json.load(f)
        existing_ids = {d["id"] for d in corpus}
        print(f"Loaded {len(corpus)} existing documents.")
    except FileNotFoundError:
        corpus = []
        existing_ids = set()
        print("No existing corpus found, starting fresh.")

    all_pages = PAGES
    to_scrape = [p for p in all_pages if p.lower().replace("%27", "").replace("'", "") not in existing_ids]
    print(f"Scraping {len(to_scrape)} new pages from Terraria Wiki...\n")

    new_docs = 0
    for i, slug in enumerate(to_scrape, 1):
        print(f"[{i:03d}/{len(to_scrape)}] {slug.replace('_', ' ')}")
        doc = fetch_page(slug)
        if doc:
            corpus.append(doc)
            new_docs += 1
            print(f"  OK — {doc['word_count']} words [{doc['category']}]")
        time.sleep(1.5)

    print(f"\nDone. {new_docs} new documents added. Total: {len(corpus)}")

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


if __name__ == "__main__":
    main()