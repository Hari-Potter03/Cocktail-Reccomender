import { useEffect, useState } from "react";
import { postRecs } from "../lib/api";
import type { DrinkCard as Card } from "../lib/types";
import DrinkCard from "../components/cards/DrinkCard";
import { getOnboarding, getUserId } from "../lib/storage";

export default function Home() {
  const [items, setItems] = useState<Card[] | null>(null);
  const user = getUserId() || "local";
  useEffect(() => {
    const onb = getOnboarding() || {};
    postRecs({
      user_id: user,
      likes: { spirit: onb.spirit || [], tags: onb.tags || [], season: onb.season || [] },
      dislikes: { tags: onb.avoid_tags || [] },
      k: 24,
    }).then(res => setItems(res.items)).catch(()=>setItems([]));
  }, []);
  return (
    <div className="container" style={{ paddingTop: 16 }}>
      <h2>Recommended for you</h2>
      {!items && <div>Loading…</div>}
      {items && items.length === 0 && <div>No recommendations yet.</div>}
      {items && items.length > 0 && (
        <div className="grid">
          {items.map(d => <DrinkCard key={d.id} d={d} userId={user} onRated={()=>{ /* optional: refresh profile */ }} />)}
        </div>
      )}
    </div>
  );
}
