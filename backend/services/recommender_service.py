import numpy as np
from .similarity import cosine_all, topk

def _zero_vec(dim): return np.zeros((dim,), dtype=np.float32)

def build_query_vec(reg, likes=None, dislikes=None, seed_ids=None):
    likes = likes or {}; dislikes = dislikes or {}; seed_ids = seed_ids or []
    v = _zero_vec(reg.dim)

    # helper to set one-hot blocks by vocab name
    def set_one(block, vocab_key, names, weight=1.0):
        if not names: return
        vocab = reg.id_map["vocab"][vocab_key]
        off = reg.offsets[block]
        for name in names:
            name = (name or "").lower()
            if name in vocab:
                v[off + vocab.index(name)] = max(v[off + vocab.index(name)], weight)

    # apply likes
    set_one("spirit", "spirit", likes.get("spirit"))
    set_one("tags",   "tags",   likes.get("tags"))
    set_one("season", "season", likes.get("season"))

    # apply dislikes as small negatives
    def set_neg(block, vocab_key, names, weight=-0.5):
        if not names: return
        vocab = reg.id_map["vocab"][vocab_key]; off = reg.offsets[block]
        for name in names:
            n=(name or "").lower()
            if n in vocab: v[off + vocab.index(n)] = min(v[off + vocab.index(n)], weight)
    set_neg("tags","tags",dislikes.get("tags"))
    set_neg("season","season",dislikes.get("season"))

    # seed ids: average their vectors
    if seed_ids:
        rows = [reg.index_by_id[s] for s in seed_ids if s in reg.index_by_id]
        if rows:
            seed_mean = reg.vectors[rows].mean(axis=0)
            v = v + 0.7*seed_mean  # blend

    # L2 normalize (safe)
    n = np.linalg.norm(v)
    return v if n==0 else (v / n).astype(np.float32)

def similar(reg, drink_id: str, k=20):
    ix = reg.index_by_id.get(drink_id)
    if ix is None: return []
    scores = cosine_all(reg.vectors, reg.vectors[ix])
    idx, _ = topk(scores, k, exclude_idx=ix)
    return [reg.ids[i] for i in idx]

def recommend(reg, likes=None, dislikes=None, seed_ids=None, k=48):
    q = build_query_vec(reg, likes, dislikes, seed_ids)
    scores = cosine_all(reg.vectors, q)
    idx, _ = topk(scores, k)
    return [reg.ids[i] for i in idx]
