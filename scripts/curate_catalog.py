#!/usr/bin/env python3
"""
Curate TheCocktailDB raw snapshot → data/curated/drinks_catalog.json

Adds:
- brands, primary_spirit_brand, season, alcoholic flag
- Stronger primary_spirit detection (spirits first; fallback to secondary bases)
"""

import json, re, glob
from datetime import datetime, timezone
from pathlib import Path
from fractions import Fraction

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/curated")
OUT_FILE = OUT_DIR / "drinks_catalog.json"
MANIFEST = OUT_DIR / "manifest.json"

# ---------------- Controlled vocabularies ---------------- #

# Primary spirit families (strict)
BASE_SPIRITS = {
    "tequila":  ["tequila", "blanco", "reposado", "añejo", "anejo"],
    "mezcal":   ["mezcal"],
    "rum":      ["rum", "white rum", "light rum", "dark rum", "gold rum", "aged rum", "spiced rum", "overproof rum", "cachaça", "cachaca"],
    "gin":      ["gin", "london dry", "old tom", "navy strength", "genever"],
    "vodka":    ["vodka"],
    "whiskey":  ["whiskey", "whisky", "irish whiskey", "tennessee whiskey", "canadian whisky", "japanese whisky"],
    "bourbon":  ["bourbon"],
    "rye":      ["rye", "rye whiskey", "rye whisky"],
    "scotch":   ["scotch", "blended scotch", "single malt"],
    "brandy":   ["brandy", "cognac", "armagnac", "pisco", "calvados", "applejack"],
    # Neutral/high-proof
    "neutral":  ["everclear", "grain alcohol", "neutral grain spirit", "rectified spirit"],
}

# Secondary base families (fallback if no primary spirit found)
SECONDARY_BASES = {
    "liqueur": {
        "amaretto","kahlua","sambuca","midori","frangelico","grand marnier",
        "triple sec","cointreau","curaçao","curacao","maraschino","chartreuse",
        "baileys","creme de cacao","crème de cacao","creme de menthe","crème de menthe",
        "falernum","amaro","limoncello","st germain","st-germain","drambuie",
        "chambord","raspberry liqueur","chocolate liqueur","godiva liqueur",
        "peach schnapps","strawberry schnapps","schnapps","goldschlager","goldschläger"
    },
    "fortified_wine": {"vermouth","sherry","port"},
    "wine": {"champagne","prosecco","red wine","white wine","wine"},
    "beer_cider": {"beer","lager","ale","stout","cider"},
    "sake_soju": {"sake","soju"},
}

# brand token -> canonical brand
BRAND_CANON = {
    "cointreau": "Cointreau",
    "grand marnier": "Grand Marnier",
    "campari": "Campari",
    "aperol": "Aperol",
    "kahlua": "Kahlúa",
    "baileys": "Baileys",
    "frangelico": "Frangelico",
    "midori": "Midori",
    "sambuca": "Sambuca",
    "st germain": "St-Germain",
    "st-germain": "St-Germain",
    "chartreuse": "Chartreuse",
    "angostura": "Angostura",
    "jack daniels": "Jack Daniel's",
    "absolut": "Absolut",
    "skyy": "SKYY",
    "grey goose": "Grey Goose",
    "ketel one": "Ketel One",
    "bacardi": "Bacardi",
    "havana club": "Havana Club",
    "mount gay": "Mount Gay",
    "goslings": "Goslings",
    "hennessy": "Hennessy",
    "remy martin": "Rémy Martin",
    "courvoisier": "Courvoisier",
    "jameson": "Jameson",
    "johnnie walker": "Johnnie Walker",
    "dewars": "Dewar's",
    "makers mark": "Maker's Mark",
    "bulleit": "Bulleit",
    "southern comfort": "Southern Comfort",
    "chambord": "Chambord",
    "godiva": "Godiva",
    "goldschlager": "Goldschläger",
    "goldschläger": "Goldschläger",
}

# optional: brand → spirit (for primary_spirit_brand)
BRAND_TO_SPIRIT = {
    "Jack Daniel's": "whiskey",
    "Absolut": "vodka", "SKYY": "vodka", "Grey Goose": "vodka", "Ketel One": "vodka",
    "Bacardi": "rum", "Havana Club": "rum", "Mount Gay": "rum", "Goslings": "rum",
    "Hennessy": "brandy", "Rémy Martin": "brandy", "Courvoisier": "brandy",
    "Jameson": "whiskey", "Johnnie Walker": "scotch", "Dewar's": "scotch",
    "Maker's Mark": "bourbon", "Bulleit": "bourbon",
    # Southern Comfort is a whiskey liqueur—left unmapped intentionally.
}

# Mixers/modifiers we do NOT consider primary spirits in the first pass
NON_BASE_MODIFIERS = {
    "simple syrup","rich syrup","sugar","honey","agave syrup","maple syrup","grenadine","orgeat",
    "cream","heavy cream","coconut cream","milk","yoghurt","egg","egg white","whipped cream","half and half","half-and-half","sherbet",
    "lime juice","lemon juice","orange juice","grapefruit juice","pineapple juice","cranberry juice",
    "apple juice","sour mix","lemonade","soda water","club soda","sparkling water","seltzer","water",
    "coffee","espresso","tea","cocoa powder","chocolate","cinnamon","nutmeg","vanilla extract",
}

# synonyms → canonical ingredient names
ING_SYNONYMS = {
    "lime juice": ["fresh lime juice","lime","lime cordial"],
    "lemon juice": ["fresh lemon juice","lemon"],
    "orange juice": ["oj"],
    "simple syrup": ["sugar syrup","rich syrup","gum syrup"],
    "agave syrup": ["agave nectar"],
    "ginger beer": ["ginger ale"],
    "triple sec": ["cointreau","curaçao","curacao","orange liqueur","grand marnier"],
    "bitters": ["angostura bitters","aromatic bitters","orange bitters"],
    "vermouth": ["sweet vermouth","dry vermouth","bianco vermouth"],
    "amaro": ["campari","aperol","fernet","amaro"],
    "coffee": ["espresso","cold brew"],
    "cream": ["heavy cream","coconut cream","half and half","half-and-half","whipped cream"],
    "soda water": ["club soda","sparkling water","seltzer"],
    "creme de cacao": ["crème de cacao"],
    "creme de menthe": ["crème de menthe"],
}

FLAVOR_TAGS = ["citrusy","sweet","sour","bitter","herbal","smoky","spicy","creamy","fruity","boozy","coffee","chocolate","nutty"]

CITRUS_TOKENS = {"lime","lemon","grapefruit","orange","yuzu","citron","calamansi"}
SWEET_TOKENS  = {"simple syrup","rich syrup","sugar","honey","agave syrup","maple syrup","orgeat","grenadine","liqueur","triple sec","curaçao","curacao"}
BITTER_TOKENS = {"bitters","amaro","campari","aperol","fernet","suze"}
HERBAL_TOKENS = {"mint","basil","rosemary","thyme","sage","chartreuse","absinthe"}
SMOKY_TOKENS  = {"mezcal","peated","islay","lapsang"}
SPICY_TOKENS  = {"ginger","ginger beer","chili","jalapeño","jalapeno"}
CREAMY_TOKENS = {"cream","coconut cream","egg white","milk"}
FRUITY_TOKENS = {"pineapple","passion","mango","strawberry","peach","apple","banana","coconut","pomegranate","berry"}
COFFEE_TOKENS = {"coffee","espresso"}
CHOC_TOKENS   = {"cacao","chocolate","creme de cacao","crème de cacao"}
NUTTY_TOKENS  = {"orgeat","almond","hazelnut","amaretto","walnut"}

TECHNIQUES = ["shake","stir","blend","build"]
SEASONS = ["spring","summer","fall","winter","holiday"]

# ---------------- Utils ---------------- #

def load_latest_raw(path=None):
    if path:
        with Path(path).open("r", encoding="utf-8") as f:
            return json.load(f)
    files = sorted(glob.glob(str(RAW_DIR / "cocktails_*.json")))
    if not files:
        raise FileNotFoundError("No raw snapshots in data/raw/")
    with open(files[-1], "r", encoding="utf-8") as f:
        return json.load(f)

def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def normalize_ingredient(name):
    if not name: return None
    t = norm_text(name)
    t = re.sub(r"[^\w\s&/-]", "", t)
    for canon, alts in ING_SYNONYMS.items():
        for a in alts:
            if t == norm_text(a):
                return canon
    return t

def extract_ing_and_measures(rec):
    out = []
    for i in range(1, 16):
        ing = rec.get(f"strIngredient{i}")
        if ing and ing.strip():
            n = normalize_ingredient(ing)
            meas = rec.get(f"strMeasure{i}")
            out.append((n, norm_text(meas) if meas else None))
    return out

def _wb(word: str, text: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None

def parse_amount_ml(measure: str | None) -> float:
    if not measure: return 0.0
    s = measure.lower().replace("½","1/2").replace("¼","1/4").replace("¾","3/4")
    m = re.findall(r"(\d+(?:\s+\d+/\d+|/\d+)?)\s*([a-z]+)", s)
    if not m:
        if "dash" in s: return 1.0
        if "splash" in s: return 5.0
        if "shot" in s or "jigger" in s: return 44.0
        return 0.0
    qty_str, unit = m[0]
    parts = qty_str.split()
    try:
        qty = float(sum(Fraction(p) for p in parts))
    except Exception:
        qty = float(parts[0])
    unit = unit.rstrip("s")
    if unit == "oz": return qty * 29.57
    if unit == "ml": return qty
    if unit == "cl": return qty * 10.0
    if unit == "tsp": return qty * 4.93
    if unit == "tbsp": return qty * 14.79
    if unit == "dash": return qty * 1.0
    if unit == "splash": return qty * 5.0
    if unit in {"shot","jigger"}: return qty * 44.0
    return 0.0

# Alcoholic flag from source
def get_alcoholic_flag(rec):
    v = (rec.get("strAlcoholic") or "").strip().lower()
    if "non" in v and "alcoholic" in v:
        return "non_alcoholic"
    if "optional" in v:
        return "optional"
    return "alcoholic"

# ---------------- Derivations ---------------- #

def extract_brands(ingredients: list[str]) -> list[str]:
    found = set()
    for ing in ingredients:
        for token, canon in BRAND_CANON.items():
            if _wb(token, ing):
                found.add(canon)
    return sorted(found)

def guess_primary_spirit(ing_meas_pairs):
    """
    1) Try true spirits first (BASE_SPIRITS + brand→spirit), measure-weighted.
    2) If none found, fall back to SECONDARY_BASES categories (liqueur, fortified_wine, wine, beer_cider, sake_soju).
    3) If two spirits tie and both sizeable, return 'blend'.
    """
    totals = {}     # spirit -> ml
    first_idx = {}  # spirit -> first position

    for idx, (ing, meas) in enumerate(ing_meas_pairs):
        if not ing: continue
        text = ing

        # Skip obvious mixers when searching for spirits
        if text in NON_BASE_MODIFIERS or any(_wb(m, text) for m in NON_BASE_MODIFIERS):
            continue

        # brand hint → spirit
        for token, canon in BRAND_CANON.items():
            if _wb(token, text):
                spirit = BRAND_TO_SPIRIT.get(canon)
                if spirit:
                    ml = parse_amount_ml(meas)
                    totals[spirit] = totals.get(spirit, 0.0) + ml
                    first_idx.setdefault(spirit, idx)

        # explicit spirit tokens
        for spirit, tokens in BASE_SPIRITS.items():
            for tok in tokens:
                if _wb(tok, text):
                    ml = parse_amount_ml(meas)
                    totals[spirit] = totals.get(spirit, 0.0) + ml
                    first_idx.setdefault(spirit, idx)

    if totals:
        if all(v == 0.0 for v in totals.values()):
            return min(first_idx.items(), key=lambda kv: kv[1])[0]
        top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
        if len(top) >= 2 and top[1][1] >= top[0][1] - 10 and top[0][1] >= 25 and top[1][1] >= 25:
            return "blend"
        return top[0][0]

    # ---- Secondary fallback ----
    sec_totals = {}  # category -> ml
    for _, (ing, meas) in enumerate(ing_meas_pairs):
        if not ing: continue
        text = ing
        ml = parse_amount_ml(meas)
        for cat, tokens in SECONDARY_BASES.items():
            for tok in tokens:
                if _wb(tok, text):
                    sec_totals[cat] = sec_totals.get(cat, 0.0) + (ml if ml else 1.0)

    if sec_totals:
        return max(sec_totals.items(), key=lambda kv: kv[1])[0]

    return None

def guess_primary_spirit_brand(primary_spirit: str | None, ingredients: list[str], ing_meas_pairs):
    if not primary_spirit: return None
    scores = {}
    for (ing, meas) in ing_meas_pairs:
        for token, canon in BRAND_CANON.items():
            if _wb(token, ing):
                mapped = BRAND_TO_SPIRIT.get(canon)
                if mapped == primary_spirit:
                    scores[canon] = scores.get(canon, 0.0) + parse_amount_ml(meas)
    return max(scores, key=scores.get) if scores else None

def guess_technique(instructions):
    if not instructions:
        return None
    txt = norm_text(instructions)
    for tech in TECHNIQUES:
        if tech in txt:
            return tech
    if "pour" in txt or "build" in txt:
        return "build"
    return None

def has_any(ingredients, token_set):
    return any(any(tok in ing for tok in token_set) for ing in ingredients)

def derive_flavors_and_taste(ingredients):
    tags = set()
    taste = dict.fromkeys(["sweet","sour","bitter","boozy","herbal","smoky","spicy","creamy","fruity"], 0.0)
    if has_any(ingredients, CITRUS_TOKENS): tags.add("citrusy"); taste["sour"] = max(taste["sour"], 0.6)
    if has_any(ingredients, SWEET_TOKENS):  tags.add("sweet");   taste["sweet"] = max(taste["sweet"], 0.6)
    if has_any(ingredients, BITTER_TOKENS): tags.add("bitter");  taste["bitter"] = max(taste["bitter"], 0.6)
    if has_any(ingredients, HERBAL_TOKENS): tags.add("herbal");  taste["herbal"] = max(taste["herbal"], 0.6)
    if has_any(ingredients, SMOKY_TOKENS):  tags.add("smoky");   taste["smoky"] = max(taste["smoky"], 0.7)
    if has_any(ingredients, SPICY_TOKENS):  tags.add("spicy");   taste["spicy"] = max(taste["spicy"], 0.6)
    if has_any(ingredients, CREAMY_TOKENS): tags.add("creamy")
    if has_any(ingredients, FRUITY_TOKENS): tags.add("fruity")
    if has_any(ingredients, COFFEE_TOKENS): tags.add("coffee")
    if has_any(ingredients, CHOC_TOKENS):   tags.add("chocolate")
    if has_any(ingredients, NUTTY_TOKENS):  tags.add("nutty")

    mixers = {"juice","soda","syrup","beer","wine","cordial","puree","cream","milk"}
    has_mixer = any(any(m in ing for m in mixers) for ing in ingredients)
    spirit_mentions = sum(1 for ing in ingredients for s in BASE_SPIRITS for t in BASE_SPIRITS[s] if _wb(t, ing))
    taste["boozy"] = 0.8 if (spirit_mentions >= 2 and not has_mixer) else (0.5 if spirit_mentions >= 1 else 0.2)

    for k in taste:
        taste[k] = round(min(1.0, max(0.0, taste[k])), 2)
    return sorted(tags), taste

def derive_season(ingredients, tags, technique, glass, name_text, instr_text):
    seasons = set()
    ing_set = " ".join(ingredients)
    def any_tok(toks): return any(t in ing_set for t in toks)

    if "citrusy" in tags or "fruity" in tags or any_tok({"pineapple","coconut","passion","mango"}) or (glass and glass.lower() in {"tiki","highball","collins"}) or technique in {"shake","blend"}:
        seasons.add("summer")
    if "creamy" in tags or "coffee" in tags or "chocolate" in tags or ("boozy" in tags and technique in {"stir","build"}) or any_tok({"cream","egg","espresso","hot","mulled"}):
        seasons.add("winter")
    if any_tok({"apple","cider","maple","cinnamon","nutmeg","cranberry","pumpkin"}):
        seasons.add("fall")
    if "herbal" in tags or any_tok({"mint","basil","cucumber","elderflower","st germain","st-germain"}):
        seasons.add("spring")
    t = (name_text + " " + instr_text).lower()
    if any(w in t for w in ["eggnog","mulled","nog","peppermint","allspice","holiday","christmas"]):
        seasons.add("holiday")
    return sorted(seasons)

# ---------------- Curation ---------------- #

def curate_record(rec):
    ing_meas = extract_ing_and_measures(rec)
    ingredients = [ing for ing,_ in ing_meas if ing]
    alcoholic_flag = get_alcoholic_flag(rec)

    primary = guess_primary_spirit(ing_meas)
    # fallback: clear NA drinks should not stay unknown
    if primary is None and alcoholic_flag != "alcoholic":
        primary = "non_alcoholic"

    technique = guess_technique(rec.get("strInstructions") or "")
    tags, taste = derive_flavors_and_taste(ingredients)
    brands = extract_brands(ingredients)
    primary_brand = guess_primary_spirit_brand(primary, ingredients, ing_meas)
    seasons = derive_season(
        ingredients=ingredients,
        tags=tags,
        technique=technique,
        glass=(rec.get("strGlass") or ""),
        name_text=(rec.get("strDrink") or ""),
        instr_text=(rec.get("strInstructions") or ""),
    )
    return {
        "id": rec.get("idDrink"),
        "name": rec.get("strDrink"),
        "alcoholic": alcoholic_flag,               # NEW
        "primary_spirit": primary,                 # may be 'blend', secondary base, or 'non_alcoholic'
        "primary_spirit_brand": primary_brand,
        "ingredients": ingredients,
        "brands": brands,
        "technique": technique,
        "glass": rec.get("strGlass"),
        "tags": tags,
        "taste_profile": taste,
        "season": seasons,
        "abv_estimate": None,
        "difficulty": None,
        "image_url": rec.get("strDrinkThumb"),
        "source_attribution": "TheCocktailDB snapshot",
    }

def main(in_path=None):
    raw = load_latest_raw(in_path)
    records = list(raw.values()) if isinstance(raw, dict) else raw
    curated = [curate_record(r) for r in records]
    curated = [c for c in curated if c["name"]]
    curated.sort(key=lambda x: (x["primary_spirit"] or "zzz", x["name"].lower()))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(curated, f, ensure_ascii=False, indent=2)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file_count": 1,
        "records_in": len(records),
        "records_out": len(curated),
        "null_primary_spirit": sum(1 for c in curated if c["primary_spirit"] is None),
        "blend_count": sum(1 for c in curated if c["primary_spirit"] == "blend"),
        "with_brands": sum(1 for c in curated if c.get("brands")),
        "secondary_bases_used": sum(1 for c in curated if c["primary_spirit"] in SECONDARY_BASES.keys()),
        "non_alcoholic_count": sum(1 for c in curated if c.get("alcoholic") == "non_alcoholic"),
    }
    with MANIFEST.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Curated {manifest['records_out']} drinks → {OUT_FILE}")
    print(f"Manifest → {MANIFEST}")
    print(
        "Missing primary_spirit:", manifest["null_primary_spirit"],
        "| blend:", manifest["blend_count"],
        "| with brands:", manifest["with_brands"],
        "| secondary bases used:", manifest["secondary_bases_used"],
        "| non-alcoholic:", manifest["non_alcoholic_count"],
    )

if __name__ == "__main__":
    main()
