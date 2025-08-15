import re
TOKEN = re.compile(r"[a-z0-9]+")

def tokenize(s: str): return TOKEN.findall((s or "").lower())

def search(reg, q: str, spirit: str|None=None, tag: str|None=None, season: str|None=None):
    idx = reg.search_index
    if q:
        toks = tokenize(q)
        if not toks: candidates = set()
        else:
            lists = [set(idx["tok2ids"].get(t, [])) for t in toks]
            candidates = set.intersection(*lists) if lists else set()
    else:
        candidates = set(reg.ids)

    if spirit:
        candidates &= set(idx["by_spirit"].get(spirit.lower(), []))
    if tag:
        candidates &= set(idx["by_tag"].get(tag.lower(), []))
    if season:
        candidates &= set(idx["by_season"].get(season.lower(), []))

    # stable order by name
    items = sorted((reg.catalog[i] for i in candidates), key=lambda r: (r.get("name") or "").lower())
    return items

def facets(reg):
    si = reg.search_index
    def counts(d): return {k: len(v) for k, v in d.items()}
    return {
        "spirits": counts(si["by_spirit"]),
        "tags": counts(si["by_tag"]),
        "seasons": counts(si["by_season"]),
        "total": len(reg.ids),
    }
