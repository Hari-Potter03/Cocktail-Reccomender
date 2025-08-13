from pathlib import Path
import json, numpy as np
from datetime import datetime, timezone

class Registry:
    def __init__(self, config_path="config/app.json"):
        self.cfg = json.loads(Path(config_path).read_text())
        p = self.cfg["paths"]
        recs_cfg = self.cfg.get("recs", {})

        # curated catalog
        self.catalog_list = json.loads(Path(p["catalog"]).read_text())
        self.catalog = {r["id"]: r for r in self.catalog_list}

        # features
        self.vectors = np.array(json.loads(Path(p["vectors"]).read_text()), dtype=np.float32)
        self.id_map = json.loads(Path(p["id_map"]).read_text())
        self.ids = self.id_map["ids"]
        self.index_by_id = {did: i for i, did in enumerate(self.ids)}
        self.dim = self.id_map["dim"]
        self.blocks = self.id_map["block_sizes"]

        # block offsets in concatenation order
        self.offsets = {}
        off = 0
        for k in ["spirit","tags","season","taste","ingredients","brands"]:
            self.offsets[k] = off
            off += self.blocks[k]

        # search index
        self.search_index = json.loads(Path(p["search_index"]).read_text())

        # storage paths
        self.ratings_path = Path(p["ratings"]); self.ratings_path.parent.mkdir(parents=True, exist_ok=True)
        self.profile_path = Path(p["profile"]); self.profile_path.parent.mkdir(parents=True, exist_ok=True)

        # blend weights + diversity
        w = recs_cfg.get("weights", {})
        self.weight_content = float(w.get("content", 0.4))
        self.weight_taste   = float(w.get("taste",   0.6))
        self.weight_als     = float(w.get("als",     0.0))
        self.diversity_penalty = float(recs_cfg.get("diversity_penalty", 0.12))

        # optional ALS pointer path
        self.als_active_path = Path(p.get("als_active", "models/als/active.json"))

    def now_iso(self):  # small helper
        return datetime.now(timezone.utc).isoformat()

    def get(self, drink_id: str):
        return self.catalog.get(drink_id)

    def row(self, drink_id: str):
        ix = self.index_by_id.get(drink_id)
        return None if ix is None else self.vectors[ix]
