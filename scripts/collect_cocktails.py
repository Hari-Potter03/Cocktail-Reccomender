#!/usr/bin/env python3
"""
Build a large local snapshot from TheCocktailDB (free key '1').

- Sweeps A–Z/0–9 via search.php?f=
- Sweeps categories, glasses, alcoholic flags via list.php + filter.php
- Sweeps ingredients via list.php?i=list + filter.php?i=
- Hydrates full records with lookup.php?i=
- Dedupes by idDrink
- Saves raw JSON (canonical). Optional: flattened CSV for quick viewing.
"""

import argparse, json, os, string, time, csv
from datetime import datetime
import requests

BASE = "https://www.thecocktaildb.com/api/json/v1/1"

def safe_get(path, params=None, retries=3, backoff=0.8, delay=0.25, timeout=30):
    url = f"{BASE}/{path}"
    err = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params or {}, timeout=timeout)
            r.raise_for_status()
            time.sleep(delay)  # be polite
            return r.json()
        except Exception as e:
            err = e
            time.sleep(backoff * (attempt + 1))
    raise err

def sweep_letters():
    drinks = {}
    letters = list(string.ascii_lowercase) + list(string.digits)
    for ch in letters:
        data = safe_get("search.php", {"f": ch})
        for d in (data.get("drinks") or []):
            drinks[d["idDrink"]] = d
    return drinks

def list_values(kind):
    # kind: 'c' (category), 'g' (glass), 'a' (alcoholic), 'i' (ingredient)
    key_map = {"c": "strCategory", "g": "strGlass", "a": "strAlcoholic", "i": "strIngredient1"}
    data = safe_get("list.php", {kind: "list"})
    return [row[key_map[kind]] for row in (data.get("drinks") or [])]

def filter_ids(param, value):
    data = safe_get("filter.php", {param: value})
    return [row["idDrink"] for row in (data.get("drinks") or [])]

def hydrate_ids(ids, delay=0.25):
    out = {}
    for did in ids:
        rec = safe_get("lookup.php", {"i": did}, delay=delay).get("drinks") or []
        if rec:
            out[rec[0]["idDrink"]] = rec[0]
    return out

def save_json(drinks_by_id, path, pretty=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(drinks_by_id, f, ensure_ascii=False, indent=2 if pretty else None)
    print(f"Saved {len(drinks_by_id):,} drinks → {path}")

def flatten_row(d):
    ing = [d.get(f"strIngredient{i}") for i in range(1, 16)]
    meas = [d.get(f"strMeasure{i}")    for i in range(1, 16)]
    ing = [x.strip() for x in ing if x and x.strip()]
    meas = [x.strip() for x in meas if x and x.strip()]
    return {
        "id": d.get("idDrink"),
        "name": d.get("strDrink"),
        "category": d.get("strCategory"),
        "alcoholic": d.get("strAlcoholic"),
        "glass": d.get("strGlass"),
        "ingredients": "; ".join(ing),
        "measures": "; ".join(meas),
        "thumb": d.get("strDrinkThumb"),
        "instructions": (d.get("strInstructions") or "").replace("\n", " ").strip(),
    }

def save_csv(drinks_by_id, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = ["id","name","category","alcoholic","glass","ingredients","measures","thumb","instructions"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for d in drinks_by_id.values():
            w.writerow(flatten_row(d))
    print(f"Saved CSV → {path}")

def main():
    ap = argparse.ArgumentParser(description="CocktailDB bulk snapshot (JSON canonical; optional CSV).")
    today = datetime.utcnow().strftime("%Y%m%d")
    ap.add_argument("--out-json", default=f"data/raw/cocktails_{today}.json")
    ap.add_argument("--out-csv", default=None, help="Optional flattened CSV path (e.g., data/raw/cocktails_flat.csv)")
    ap.add_argument("--delay", type=float, default=0.25, help="Delay between requests (seconds)")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--max-ingredients", type=int, default=None, help="Limit ingredient sweep for faster tests")
    args = ap.parse_args()

    # 1) A–Z / 0–9
    print("Sweeping A–Z and 0–9 …")
    drinks = sweep_letters()
    print(f"After letters: {len(drinks):,}")

    # 2) Categories, Glasses, Alcoholic flags
    for param, label in (("c","categories"),("g","glasses"),("a","alcoholic flags")):
        print(f"Sweeping {label} …")
        for v in list_values(param):
            ids = filter_ids(param, v)
            missing = [i for i in ids if i not in drinks]
            if not missing: continue
            hydrated = hydrate_ids(missing, delay=args.delay)
            drinks.update(hydrated)
        print(f"After {label}: {len(drinks):,}")

    # 3) Ingredients (bigger pass)
    print("Sweeping ingredients (this can take a while) …")
    ingredients = list_values("i")
    if args.max_ingredients:
        ingredients = ingredients[: args.max_ingredients]
    for idx, ing in enumerate(ingredients, 1):
        ids = filter_ids("i", ing)
        missing = [i for i in ids if i not in drinks]
        if missing:
            drinks.update(hydrate_ids(missing, delay=args.delay))
        if idx % 50 == 0:
            print(f"  {idx}/{len(ingredients)} ingredients → total drinks: {len(drinks):,}")

    # Save outputs
    save_json(drinks, args.out_json, pretty=True)
    if args.out_csv:
        save_csv(drinks, args.out_csv)
    print("Done. Next: curate to data/curated/drinks_catalog.json.")
    
if __name__ == "__main__":
    main()