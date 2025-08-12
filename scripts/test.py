# scripts/audit_primary_spirit_gaps.py
import json, re, collections
raw = json.load(open("data/curated/drinks_catalog.json"))
unknown = [d for d in raw if d["primary_spirit"] is None]
tokcounts = collections.Counter()
for d in unknown:
    for ing in d["ingredients"]:
        for t in re.findall(r"[a-zA-Z]+(?:\s[a-zA-Z]+)?", ing):
            tokcounts[t.lower()] += 1
print("Top tokens in unknowns:")
for w,c in tokcounts.most_common(50):
    print(f"{w:20} {c}")
