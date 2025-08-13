import json, os
from pathlib import Path
import numpy as np

def _zero(dim): return np.zeros((dim,), dtype=np.float32)

def load_all_ratings(ratings_path: Path, user_id: str = "local"):
    if not ratings_path.exists():
        return []
    out = []
    with ratings_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                obj = json.loads(line)
                if (obj.get("user_id") or "local") == user_id:
                    out.append(obj)
            except Exception:
                continue
    return out

def compute_taste_vector(reg, ratings: list, like_threshold=4.0, dislike_threshold=2.0):
    """Average positives minus a small average of dislikes; L2 normalize."""
    pos_rows, neg_rows = [], []
    for r in ratings:
        rid = r.get("drink_id")
        if rid in reg.index_by_id:
            ix = reg.index_by_id[rid]
            if float(r.get("rating", 0)) >= like_threshold:
                pos_rows.append(ix)
            elif float(r.get("rating", 0)) <= dislike_threshold:
                neg_rows.append(ix)

    if not pos_rows and not neg_rows:
        return None

    v = _zero(reg.dim)
    if pos_rows:
        v += reg.vectors[pos_rows].mean(axis=0)
    if neg_rows:
        v -= 0.5 * reg.vectors[neg_rows].mean(axis=0)

    n = float(np.linalg.norm(v))
    return (v / n).astype(np.float32) if n > 0 else None

def _top_from_block(vec, vocab, offset, k=3):
    block = vec[offset:offset+len(vocab)]
    idx = np.argsort(-block)[:k]
    return [(vocab[i], float(block[i])) for i in idx if block[i] > 0]

def summarize_taste(reg, taste_vec):
    """Human summary for /profile."""
    vocab = reg.id_map["vocab"]
    off = reg.offsets
    spirit_top = _top_from_block(taste_vec, vocab["spirit"], off["spirit"], k=1)
    tags_top   = _top_from_block(taste_vec, vocab["tags"],   off["tags"],   k=4)
    seasons    = _top_from_block(taste_vec, vocab["season"], off["season"], k=3)
    return {
        "primary_spirit": spirit_top[0][0] if spirit_top else None,
        "top_tags": [t for t,_ in tags_top],
        "top_seasons": [s for s,_ in seasons],
    }

def load_profiles(profile_path: Path):
    if not profile_path.exists():
        return {}
    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_profiles(profile_path: Path, data: dict):
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def rebuild_and_save_profile(reg, user_id="local"):
    """Recompute taste vec from ratings, persist to storage/profiles.json, return summary."""
    ratings = load_all_ratings(reg.ratings_path, user_id)
    taste_vec = compute_taste_vector(reg, ratings)
    profiles = load_profiles(reg.profile_path)
    profiles[user_id] = {
        "has_taste": bool(taste_vec is not None),
        "taste_vec": taste_vec.tolist() if taste_vec is not None else None,
        "ratings_count": len(ratings),
        "updated_at": reg.now_iso(),
    }
    save_profiles(reg.profile_path, profiles)
    summary = summarize_taste(reg, taste_vec) if taste_vec is not None else {}
    return {"user_id": user_id, "ratings_count": len(ratings), "summary": summary, "has_taste": taste_vec is not None}

def get_taste_vec(reg, user_id="local"):
    profiles = load_profiles(reg.profile_path)
    entry = profiles.get(user_id)
    if not entry or not entry.get("taste_vec"):
        return None
    return np.array(entry["taste_vec"], dtype=np.float32)
