import numpy as np
from .similarity import cosine_all, topk
from . import profile_service as prof

def _zero_vec(dim): return np.zeros((dim,), dtype=np.float32)

def build_query_vec(reg, likes=None, dislikes=None, seed_ids=None):
    likes = likes or {}; dislikes = dislikes or {}; seed_ids = seed_ids or []
    v = _zero_vec(reg.dim)

    def set_one(block, vocab_key, names, weight=1.0):
        if not names: return
        vocab = reg.id_map["vocab"][vocab_key]
        off = reg.offsets[block]
        for name in names:
            name = (name or "").lower()
            if name in vocab:
                j = off + vocab.index(name)
                v[j] = max(v[j], weight)

    # likes
    set_one("spirit", "spirit", likes.get("spirit"))
    set_one("tags",   "tags",   likes.get("tags"))
    set_one("season", "season", likes.get("season"))

    # dislikes: push down a bit
    def set_neg(block, vocab_key, names, weight=-0.5):
        if not names: return
        vocab = reg.id_map["vocab"][vocab_key]; off = reg.offsets[block]
        for name in names:
            n=(name or "").lower()
            if n in vocab:
                j = off + vocab.index(n)
                v[j] = min(v[j], weight)
    set_neg("tags","tags",dislikes.get("tags"))
    set_neg("season","season",dislikes.get("season"))

    # seed ids average
    rows = [reg.index_by_id[s] for s in (seed_ids or []) if s in reg.index_by_id]
    if rows:
        seed_mean = reg.vectors[rows].mean(axis=0)
        v = v + 0.7*seed_mean

    n = np.linalg.norm(v)
    return v if n==0 else (v / n).astype(np.float32)

def _spirit_of(reg, drink_id):
    rec = reg.get(drink_id) or {}
    return (rec.get("primary_spirit") or "unknown").lower()

def diversify_by_spirit(reg, ids, scores, penalty=0.12, k=None):
    """Greedy re-rank: penalize candidates that repeat same spirit too often."""
    k = k or len(ids)
    chosen, chosen_spirits, chosen_set = [], {}, set()
    # Precompute spirit for all candidates
    cand_spirit = {i: _spirit_of(reg, i) for i in ids}

    # Working copy
    rem = ids[:]
    sc_map = {i: float(scores.get(i, 0.0)) for i in ids}

    while rem and len(chosen) < k:
        # apply penalties
        adjusted = []
        for i in rem:
            s = cand_spirit[i]
            penal = penalty * chosen_spirits.get(s, 0)
            adjusted.append((i, sc_map[i] - penal))
        adjusted.sort(key=lambda x: -x[1])
        pick, _ = adjusted[0]
        chosen.append(pick)
        chosen_set.add(pick)
        s = cand_spirit[pick]
        chosen_spirits[s] = chosen_spirits.get(s, 0) + 1
        rem = [i for i in rem if i not in chosen_set]
    return chosen

def reasons_for(reg, drink_id, query_vec=None, taste_vec=None, top_k=3):
    """Simple reason chips from block overlaps."""
    vocab = reg.id_map["vocab"]; off = reg.offsets
    chips = []

    def top_overlap(block_key, vocab_key, label):
        if query_vec is None: return
        vocab_list = vocab[vocab_key]
        off_b = off[block_key]; L = len(vocab_list)
        block = query_vec[off_b:off_b+L]
        if block.max() <= 0: return
        j = int(np.argmax(block))
        chips.append(f"{label}: {vocab_list[j]}")

    top_overlap("spirit","spirit","spirit")
    top_overlap("season","season","season")

    # tags: list top 2 positives
    if query_vec is not None:
        tags_block = query_vec[off["tags"]:off["tags"]+len(vocab["tags"])]
        if tags_block.max() > 0:
            idx = np.argsort(-tags_block)[:2]
            chips.extend([f"tag: {vocab['tags'][i]}" for i in idx if tags_block[i] > 0])

    # taste: show strongest taste dim if used
    if query_vec is not None:
        tk = reg.id_map["vocab"]["taste_keys"]
        t_off = off["taste"]; block = query_vec[t_off:t_off+len(tk)]
        if block.max() > 0:
            chips.append(f"taste: {tk[int(np.argmax(block))]}")

    # If taste_vec exists, add hint
    if taste_vec is not None:
        chips.append("personalized")

    return chips[:top_k]

def recommend(reg, likes=None, dislikes=None, seed_ids=None, k=48, user_id="local"):
    # Content query
    q = build_query_vec(reg, likes, dislikes, seed_ids)
    content_scores = cosine_all(reg.vectors, q)

    # Taste vector (from ratings)
    taste_vec = prof.get_taste_vec(reg, user_id=user_id)
    taste_scores = cosine_all(reg.vectors, taste_vec) if taste_vec is not None else None

    # TODO(ALS later): als_scores = ...

    # Blend
    blend = reg.weight_content * content_scores
    if taste_scores is not None:
        blend = blend + reg.weight_taste * taste_scores
    # (ALS weight currently 0.0)

    # Top-K & diversity
    idx, raw_top = topk(blend, max(k*3, k))  # get a pool, then diversify
    cand_ids = [reg.ids[i] for i in idx]
    score_map = {reg.ids[i]: float(blend[i]) for i in idx}
    diversified = diversify_by_spirit(reg, cand_ids, score_map, penalty=reg.diversity_penalty, k=k)
    # Build results with reasons
    results = []
    for did in diversified[:k]:
        results.append({
            "id": did,
            "name": (reg.get(did) or {}).get("name"),
            "image_url": (reg.get(did) or {}).get("image_url"),
            "primary_spirit": (reg.get(did) or {}).get("primary_spirit"),
            "tags": (reg.get(did) or {}).get("tags"),
            "season": (reg.get(did) or {}).get("season"),
            "reason": reasons_for(reg, did, query_vec=q, taste_vec=taste_vec)
        })
    return results

def similar(reg, drink_id: str, k=20):
    ix = reg.index_by_id.get(drink_id)
    if ix is None: return []
    scores = cosine_all(reg.vectors, reg.vectors[ix])
    idx, _ = topk(scores, k, exclude_idx=ix)
    return [reg.ids[i] for i in idx]
