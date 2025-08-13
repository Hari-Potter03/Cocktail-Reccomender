#!/usr/bin/env python3
# ... (header docstring unchanged)

import argparse, json, os, re, math, hashlib
from collections import defaultdict, Counter
from pathlib import Path

CURATED_DIR = Path("data/curated")
FEATURE_DIR  = Path("data/features")

DEFAULT_INPUTS = [
    CURATED_DIR / "drinks_catalog_v1.json",
    CURATED_DIR / "drinks_catalog.json",
]

# ----------------- Config ----------------- #
ING_HASH_DIM   = 512
BRAND_HASH_DIM = 64

WEIGHTS = {
    "spirit": 2.0,
    "tags": 1.2,
    "season": 0.8,
    "taste": 1.5,
    "ingredients": 1.0,
    "brands": 0.6,
}

TASTE_KEYS = ["sweet","sour","bitter","boozy","herbal","smoky","spicy","creamy","fruity"]
TOKEN_RE = re.compile(r"[a-z0-9]+")

def load_curated(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = list(data.values())
    return data

def choose_input() -> Path:
    for p in DEFAULT_INPUTS:
        if p.exists():
            return p
    raise FileNotFoundError("No curated catalog found in data/curated/. Run curate_catalog.py first.")

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def tokenize(s: str) -> list[str]:
    return TOKEN_RE.findall(norm(s))

def hash_index(text: str, dim: int, salt: str = "") -> int:
    h = hashlib.sha1((salt + "§" + text).encode("utf-8")).digest()
    return int.from_bytes(h[:4], "little") % dim

def l2_normalize(vec: list[float]) -> list[float]:
    s = math.sqrt(sum(x*x for x in vec))
    if s == 0:
        return vec
    return [x / s for x in vec]

def build_vocabs(records: list[dict]):
    spirits, tags, seasons = set(), set(), set()
    for r in records:
        spirits.add((r.get("primary_spirit") or "unknown").lower())
        for t in (r.get("tags") or []): tags.add(t.lower())
        for s in (r.get("season") or []): seasons.add(s.lower())
    return sorted(spirits), sorted(tags), sorted(seasons)

def spirit_one_hot(spirit: str, vocab: list[str]) -> list[float]:
    spirit = (spirit or "unknown").lower()
    v = [0.0] * len(vocab)
    try:
        v[vocab.index(spirit)] = 1.0
    except ValueError:
        if "unknown" in vocab: v[vocab.index("unknown")] = 1.0
    return v

def multi_hot(items: list[str], vocab: list[str]) -> list[float]:
    v = [0.0] * len(vocab)
    for it in (items or []):
        it = it.lower()
        try: v[vocab.index(it)] = 1.0
        except ValueError: pass
    return v

def taste_block(taste: dict) -> list[float]:
    return [float(taste.get(k, 0.0)) for k in TASTE_KEYS]

def hashed_block(tokens: list[str], dim: int, salt: str) -> list[float]:
    if not tokens: return [0.0] * dim
    v = [0.0] * dim
    for tok in tokens:
        v[hash_index(tok, dim, salt=salt)] = 1.0
    return v

def ingredient_tokens(ingredients: list[str]) -> list[str]:
    toks = []
    for ing in (ingredients or []):
        ing = norm(ing)
        if not ing: continue
        toks.append(ing)
        toks.extend(tokenize(ing))
    return toks

def brand_tokens(brands: list[str]) -> list[str]:
    toks = []
    for b in (brands or []):
        b = norm(b)
        toks.append(b)
        toks.extend(tokenize(b))
    return toks

def build_search_index(records: list[dict], ids: list[str]):
    tok2ids: dict[str, list[str]] = defaultdict(list)
    by_spirit: dict[str, list[str]] = defaultdict(list)
    by_tag: dict[str, list[str]] = defaultdict(list)
    by_season: dict[str, list[str]] = defaultdict(list)

    for r in records:
        rid = r["id"]
        fields = []
        fields.extend(tokenize(r.get("name") or ""))
        for ing in (r.get("ingredients") or []): fields.extend(tokenize(ing))
        for br in (r.get("brands") or []): fields.extend(tokenize(br))
        fields.extend(tokenize(r.get("glass") or ""))
        fields.extend(tokenize(r.get("technique") or ""))

        seen = set()
        for t in fields:
            if t and t not in seen:
                tok2ids[t].append(rid)
                seen.add(t)

        by_spirit[(r.get("primary_spirit") or "unknown").lower()].append(rid)
        for t in (r.get("tags") or []): by_tag[t.lower()].append(rid)
        for s in (r.get("season") or []): by_season[s.lower()].append(rid)

    for d in (tok2ids, by_spirit, by_tag, by_season):
        for k in d: d[k] = sorted(d[k], key=lambda x: (x is None, x))

    return {"tok2ids": tok2ids, "by_spirit": by_spirit, "by_tag": by_tag, "by_season": by_season,
            "count": {"unique_tokens": len(tok2ids)}}

def build_vectors(records: list[dict]):
    records = sorted(records, key=lambda r: r.get("id") or "")
    ids = [r["id"] for r in records]
    spirit_vocab, tag_vocab, season_vocab = build_vocabs(records)

    vectors: list[list[float]] = []
    for r in records:
        b_spirit = spirit_one_hot(r.get("primary_spirit"), spirit_vocab)
        b_tags   = multi_hot(r.get("tags") or [], tag_vocab)
        b_season = multi_hot(r.get("season") or [], season_vocab)
        b_taste  = taste_block(r.get("taste_profile") or {})
        b_ing    = hashed_block(ingredient_tokens(r.get("ingredients") or []), ING_HASH_DIM,   "ingredients")
        b_brand  = hashed_block(brand_tokens(r.get("brands") or []),           BRAND_HASH_DIM, "brands")

        def scale(block, w): return [x * w for x in block]
        blocks = [
            scale(b_spirit, WEIGHTS["spirit"]),
            scale(b_tags,   WEIGHTS["tags"]),
            scale(b_season, WEIGHTS["season"]),
            scale(b_taste,  WEIGHTS["taste"]),
            scale(b_ing,    WEIGHTS["ingredients"]),
            scale(b_brand,  WEIGHTS["brands"]),
        ]
        vec = [x for blk in blocks for x in blk]
        vectors.append(l2_normalize(vec))

    block_sizes = {
        "spirit": len(spirit_vocab),
        "tags": len(tag_vocab),
        "season": len(season_vocab),
        "taste": len(TASTE_KEYS),
        "ingredients": ING_HASH_DIM,
        "brands": BRAND_HASH_DIM,
    }
    dim = sum(block_sizes.values())

    id_map = {
        "ids": ids,
        "dim": dim,
        "block_sizes": block_sizes,
        "weights": WEIGHTS,
        "vocab": {"spirit": spirit_vocab, "tags": tag_vocab, "season": season_vocab, "taste_keys": TASTE_KEYS},
        "hash_dims": {"ingredients": ING_HASH_DIM, "brands": BRAND_HASH_DIM},
        "version": 1,
    }
    return vectors, id_map, records

def save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def main():
    global ING_HASH_DIM, BRAND_HASH_DIM  # <-- moved to the very top of main()

    ap = argparse.ArgumentParser(description="Build content features and search index.")
    ap.add_argument("--in", dest="inp", default=None, help="Path to curated JSON (defaults to v1 then current).")
    ap.add_argument("--outdir", default=str(FEATURE_DIR), help="Output directory (default: data/features)")
    ap.add_argument("--ing-dim", type=int, default=ING_HASH_DIM, help="Ingredient hash dim (default 512)")
    ap.add_argument("--brand-dim", type=int, default=BRAND_HASH_DIM, help="Brand hash dim (default 64)")
    args = ap.parse_args()

    # allow override dims via CLI
    ING_HASH_DIM   = args.ing_dim
    BRAND_HASH_DIM = args.brand_dim

    curated_path = Path(args.inp) if args.inp else choose_input()
    records = load_curated(curated_path)

    vectors, id_map, ordered_records = build_vectors(records)
    search_index = build_search_index(ordered_records, id_map["ids"])

    outdir = Path(args.outdir)
    save_json(vectors,      outdir / "drink_vectors.json")
    save_json(id_map,       outdir / "id_map.json")
    save_json(search_index, outdir / "search_index.json")

    norms = [sum(x*x for x in v) ** 0.5 for v in vectors]
    print(f"Saved {len(vectors)} vectors → {outdir/'drink_vectors.json'}")
    print(f"Dim: {id_map['dim']} | norms mean≈{sum(norms)/len(norms):.3f} min={min(norms):.3f} max={max(norms):.3f}")
    print(f"Vocab sizes → spirit:{id_map['block_sizes']['spirit']} tags:{id_map['block_sizes']['tags']} season:{id_map['block_sizes']['season']}")
    print(f"Search tokens: {search_index['count']['unique_tokens']} | Index saved → {outdir/'search_index.json'}")

if __name__ == "__main__":
    main()
