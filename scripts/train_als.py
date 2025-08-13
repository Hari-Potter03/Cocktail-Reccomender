#!/usr/bin/env python3
"""
Modular ALS training script (class-based)

Artifacts written to: models/als/<version>/
  - item_factors.npy   (float32 [n_items, rank])
  - item_norms.npy     (float32 [n_items])
  - item_id_map.json   ({drink_id: row_index})
  - meta.json          (hyperparameters, sizes, timestamp)
And pointer:
  - models/als/active.json  -> {"path":"models/als/<version>"}

Run:
  pip install implicit numpy scipy
  python scripts/train_als.py --rank 64 --reg 0.05 --iters 30 --alpha 40 \
      --min-users 30 --min-interactions 200
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Iterable

import numpy as np
import scipy.sparse as sp

# Try to import 'implicit' nicely
try:
    from implicit.als import AlternatingLeastSquares
except Exception:  # pragma: no cover
    AlternatingLeastSquares = None


# --------------------------- Utilities ---------------------------

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(obj, path: Path) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# --------------------------- Config ---------------------------

@dataclass
class AppPaths:
    catalog: str
    vectors: str
    id_map: str
    search_index: str
    ratings: str
    profile: str
    als_active: str

    @classmethod
    def from_config(cls, cfg_path: Path) -> "AppPaths":
        cfg = read_json(cfg_path)
        p = cfg.get("paths", {})
        required = ["catalog", "vectors", "id_map", "search_index", "ratings", "profile", "als_active"]
        missing = [k for k in required if k not in p]
        if missing:
            raise KeyError(f"Missing keys in {cfg_path}: {missing}")
        return cls(**{k: p[k] for k in required})


@dataclass
class ALSParams:
    rank: int = 64
    reg: float = 0.05
    iters: int = 30
    alpha: float = 40.0
    min_users: int = 30
    min_interactions: int = 200
    like_threshold: float = 3.0   # ratings > threshold → positive signal
    tried_bonus: float = 0.10     # add small weight if tried=True
    tag: str | None = None        # version folder suffix (else timestamp)

    def as_meta(self) -> Dict:
        d = asdict(self)
        d.pop("tag", None)
        return d


# --------------------------- Data: ID Map ---------------------------

class IDMap:
    """
    Holds ordering for items. We align ALS columns to this order.
    """
    def __init__(self, ids: List[str]):
        self.ids = ids
        self.index_by_id = {did: i for i, did in enumerate(ids)}

    @classmethod
    def load(cls, path: Path) -> "IDMap":
        data = read_json(path)
        ids = data["ids"]
        return cls(ids)


# --------------------------- Data: Ratings ---------------------------

@dataclass
class RatingEvent:
    user_id: str
    drink_id: str
    rating: float
    tried: bool
    ts: int | None = None

    @classmethod
    def from_json(cls, obj: Dict) -> "RatingEvent":
        return cls(
            user_id=str(obj.get("user_id") or "local"),
            drink_id=str(obj.get("drink_id")),
            rating=float(obj.get("rating", 0)),
            tried=bool(obj.get("tried", False)),
            ts=int(obj["ts"]) if "ts" in obj and obj["ts"] is not None else None,
        )


class RatingsDataset:
    def __init__(self, rows: List[RatingEvent]):
        self.rows = rows

    @classmethod
    def load_jsonl(cls, path: Path) -> "RatingsDataset":
        if not path.exists():
            return cls([])
        out: List[RatingEvent] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    obj = json.loads(s)
                    if "drink_id" in obj:
                        out.append(RatingEvent.from_json(obj))
                except Exception:
                    # skip malformed
                    continue
        return cls(out)

    def to_implicit_csr(
        self,
        id_map: IDMap,
        like_threshold: float = 3.0,
        tried_bonus: float = 0.10,
    ) -> Tuple[sp.csr_matrix, Dict[str, int]]:
        """
        Convert explicit events → implicit positives.
        weight = max(0, (rating - like_threshold) / (5 - like_threshold)) + (tried_bonus if tried else 0)
        """
        if not self.rows:
            return sp.csr_matrix((0, len(id_map.ids))), {}

        user_index: Dict[str, int] = {}
        next_uid = 0

        data, rows, cols = [], [], []

        for ev in self.rows:
            col = id_map.index_by_id.get(ev.drink_id)
            if col is None:
                continue

            if ev.user_id not in user_index:
                user_index[ev.user_id] = next_uid
                next_uid += 1
            row = user_index[ev.user_id]

            # translate explicit rating to implicit weight
            denom = max(1e-6, 5.0 - like_threshold)
            rel = max(0.0, ev.rating - like_threshold) / denom  # [0,1]
            w = rel + (tried_bonus if ev.tried else 0.0)
            if w <= 0:
                continue

            rows.append(row)
            cols.append(col)
            data.append(w)

        if not data:
            return sp.csr_matrix((0, len(id_map.ids))), user_index

        user_item = sp.csr_matrix(
            (np.array(data, dtype=np.float32), (np.array(rows), np.array(cols))),
            shape=(len(user_index), len(id_map.ids))
        )
        return user_item, user_index


# --------------------------- Training ---------------------------

class ALSTrainer:
    def __init__(self, params: ALSParams):
        if AlternatingLeastSquares is None:
            raise RuntimeError("The 'implicit' library is not installed. Install with: pip install implicit numpy scipy")
        self.params = params

    def fit(self, item_user: sp.csr_matrix) -> np.ndarray:
        """
        Train ALS on item-user matrix. Returns item_factors [n_items, rank].
        """
        model = AlternatingLeastSquares(
            factors=self.params.rank,
            regularization=self.params.reg,
            iterations=self.params.iters,
            use_gpu=False,
        )
        model.fit(item_user, show_progress=True)
        return model.item_factors.astype(np.float32)


# --------------------------- Artifacts ---------------------------

@dataclass
class ALSArtifacts:
    root: Path = Path("models/als")

    def version_dir(self, tag: str | None = None) -> Path:
        version = tag or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return self.root / version

    def save(
        self,
        item_factors: np.ndarray,
        id_map: IDMap,
        params: ALSParams,
        n_users: int,
        interactions: int,
        version_tag: str | None = None,
    ) -> Path:
        outdir = self.version_dir(version_tag)
        ensure_dir(outdir)

        # Save factors + norms
        np.save(outdir / "item_factors.npy", item_factors)
        norms = np.linalg.norm(item_factors, axis=1)
        norms[norms == 0] = 1e-8
        np.save(outdir / "item_norms.npy", norms)

        # Save id map aligned to rows
        write_json({did: i for i, did in enumerate(id_map.ids)}, outdir / "item_id_map.json")

        # Meta
        meta = {
            "algo": "implicit-als",
            "trained_at_utc": now_utc_iso(),
            "n_items": int(item_factors.shape[0]),
            "n_users": int(n_users),
            "interactions": int(interactions),
            **params.as_meta(),
        }
        write_json(meta, outdir / "meta.json")

        # Update active pointer
        ensure_dir(self.root)
        write_json({"path": f"{outdir.as_posix()}"}, self.root / "active.json")

        return outdir


# --------------------------- Orchestration ---------------------------

class ALSPipeline:
    def __init__(self, cfg_path: Path, params: ALSParams):
        self.cfg_path = cfg_path
        self.params = params
        self.paths = AppPaths.from_config(cfg_path)
        self.id_map = IDMap.load(Path(self.paths.id_map))
        self.artifacts = ALSArtifacts()

    def run(self) -> None:
        # Load ratings
        ratings_path = Path(self.paths.ratings)
        ds = RatingsDataset.load_jsonl(ratings_path)
        if not ds.rows:
            print(f"No ratings found at {ratings_path}. Nothing to train.")
            return

        # Build user-item and item-user matrices
        user_item, users = ds.to_implicit_csr(
            self.id_map,
            like_threshold=self.params.like_threshold,
            tried_bonus=self.params.tried_bonus,
        )
        n_users, n_items = user_item.shape
        interactions = int(user_item.nnz)

        # Guards
        if n_users < self.params.min_users or interactions < self.params.min_interactions:
            print(f"Not enough data to train ALS yet: users={n_users} (need ≥{self.params.min_users}), "
                  f"interactions={interactions} (need ≥{self.params.min_interactions}).")
            return

        # Scale confidences and transpose
        item_user = (user_item.tocsr() * self.params.alpha).T.tocsr()

        print(f"Training ALS: users={n_users}, items={n_items}, "
              f"rank={self.params.rank}, reg={self.params.reg}, iters={self.params.iters}, alpha={self.params.alpha}")
        trainer = ALSTrainer(self.params)
        item_factors = trainer.fit(item_user)

        # Align/Pad safety (should already match n_items)
        if item_factors.shape[0] != n_items:
            pad = n_items - item_factors.shape[0]
            if pad > 0:
                item_factors = np.vstack([item_factors, np.zeros((pad, item_factors.shape[1]), dtype=np.float32)])

        outdir = self.artifacts.save(
            item_factors=item_factors,
            id_map=self.id_map,
            params=self.params,
            n_users=n_users,
            interactions=interactions,
            version_tag=self.params.tag,
        )

        print(f"Saved ALS artifacts → {outdir}")
        print(f"Updated active pointer → {self.artifacts.root / 'active.json'}")
        print(f"item_factors: {item_factors.shape}, users: {n_users}, interactions: {interactions}")


# --------------------------- CLI ---------------------------

def parse_args() -> Tuple[Path, ALSParams]:
    ap = argparse.ArgumentParser(description="Train ALS item factors from storage/ratings.jsonl")
    ap.add_argument("--config", default="config/app.json", help="Path to config/app.json")
    ap.add_argument("--rank", type=int, default=64, help="ALS rank (factors)")
    ap.add_argument("--reg", type=float, default=0.05, help="ALS regularization")
    ap.add_argument("--iters", type=int, default=30, help="ALS iterations")
    ap.add_argument("--alpha", type=float, default=40.0, help="Confidence scale multiplier")
    ap.add_argument("--min-users", type=int, default=30, help="Minimum distinct users to train")
    ap.add_argument("--min-interactions", type=int, default=200, help="Minimum positive interactions to train")
    ap.add_argument("--like-threshold", type=float, default=3.0, help="Ratings above this count as positive signal")
    ap.add_argument("--tried-bonus", type=float, default=0.10, help="Bonus weight if tried=True")
    ap.add_argument("--tag", default=None, help="Version tag for models/als/<tag>")
    args = ap.parse_args()

    params = ALSParams(
        rank=args.rank,
        reg=args.reg,
        iters=args.iters,
        alpha=args.alpha,
        min_users=args.min_users,
        min_interactions=args.min_interactions,
        like_threshold=args.like_threshold,
        tried_bonus=args.tried_bonus,
        tag=args.tag,
    )
    return Path(args.config), params


def main():
    if AlternatingLeastSquares is None:
        print("Error: 'implicit' library not available. Install with: pip install implicit numpy scipy")
        sys.exit(1)

    cfg_path, params = parse_args()
    pipeline = ALSPipeline(cfg_path, params)
    pipeline.run()


if __name__ == "__main__":
    main()
