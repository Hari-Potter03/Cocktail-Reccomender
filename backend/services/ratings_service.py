import json, time

def append_rating(reg, user_id, drink_id, rating, tried=False, ts=None):
    ts = ts or int(time.time())
    evt = {"user_id": user_id or "local", "drink_id": drink_id, "rating": float(rating), "tried": bool(tried), "ts": ts}
    with reg.ratings_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt) + "\n")
    return evt
