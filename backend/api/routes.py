from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from ..loaders.registry import Registry
from ..services import search_service, recommender_service, ratings_service, profile_service as prof

router = APIRouter()
REG = Registry()

class RecsBody(BaseModel):
    likes: dict | None = None
    dislikes: dict | None = None
    seed_ids: list[str] | None = None
    k: int | None = 48
    user_id: str | None = "local"

class RatingBody(BaseModel):
    user_id: str | None = "local"
    drink_id: str
    rating: float
    tried: bool | None = False
    ts: int | None = None

@router.get("/drinks")
def list_drinks(spirit: str|None=None, tag: str|None=None, season: str|None=None,
                page: int=1, page_size: int=24):
    items = search_service.search(REG, q=None, spirit=spirit, tag=tag, season=season)
    start = (page-1)*page_size
    return {"items": items[start:start+page_size], "total": len(items), "page": page}

@router.get("/drinks/{drink_id}")
def get_drink(drink_id: str):
    d = REG.get(drink_id)
    if not d: raise HTTPException(404, "Not found")
    return d

@router.get("/search")
def search(q: str = Query(""), spirit: str|None=None, tag: str|None=None, season: str|None=None,
           page: int=1, page_size: int=24):
    items = search_service.search(REG, q=q, spirit=spirit, tag=tag, season=season)
    start = (page-1)*page_size
    return {"items": items[start:start+page_size], "total": len(items), "page": page}

@router.get("/similar/{drink_id}")
def similar(drink_id: str, k: int=20):
    if drink_id not in REG.index_by_id: raise HTTPException(404, "Unknown id")
    ids = recommender_service.similar(REG, drink_id, k=k)
    return {"items": [REG.get(i) for i in ids], "source": REG.get(drink_id)}

@router.post("/recs")
def recs(body: RecsBody):
    items = recommender_service.recommend(
        REG, body.likes, body.dislikes, body.seed_ids, body.k or 48, user_id=body.user_id or "local"
    )
    return {"items": items}

@router.post("/ratings")
def rate(body: RatingBody):
    evt = ratings_service.append_rating(REG, body.user_id, body.drink_id, body.rating, body.tried, body.ts)
    # Recompute taste vector immediately for instant personalization
    summary = prof.rebuild_and_save_profile(REG, user_id=body.user_id or "local")
    return {"ok": True, "event": evt, "profile": summary}

@router.get("/profile")
def profile(user_id: str = "local"):
    # ensure profile exists / is fresh
    summary = prof.rebuild_and_save_profile(REG, user_id=user_id)
    return summary

@router.get("/facets")
def get_facets():
    from ..services.search_service import facets
    return facets(REG)

