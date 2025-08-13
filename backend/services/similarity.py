import numpy as np

def cosine_all(matrix: np.ndarray, query: np.ndarray) -> np.ndarray:
    # matrix: [N,D] L2-normalized, query: [D] (normalize if needed)
    q = query / max(np.linalg.norm(query), 1e-8)
    return matrix @ q

def topk(scores: np.ndarray, k: int, exclude_idx=None):
    if exclude_idx is not None:
        scores = scores.copy()
        scores[exclude_idx] = -1e9
    idx = np.argpartition(-scores, kth=min(k, len(scores)-1))[:k]
    idx = idx[np.argsort(-scores[idx])]
    return idx, scores[idx]
