import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { getDrinks, search, getFacets } from "../lib/api";
import type { DrinkCard as Card, FacetsResponse } from "../lib/types";
import DrinkCard from "../components/cards/DrinkCard";
import { getUserId } from "../lib/storage";

function useQuery() { const { search } = useLocation(); return useMemo(() => new URLSearchParams(search), [search]); }

export default function Browse() {
  const q = useQuery(); const nav = useNavigate();
  const [items, setItems] = useState<Card[] | null>(null);
  const [facets, setFacets] = useState<FacetsResponse | null>(null);
  const page = Number(q.get("page") || 1);
  const user = getUserId() || "local";

  const fetchData = async () => {
    setItems(null);
    const params = { spirit: q.get("spirit") || undefined, tag: q.get("tag") || undefined, season: q.get("season") || undefined, page, page_size: 24 };
    if (q.get("q")) setItems((await search({ ...params, q: q.get("q")! })).items);
    else setItems((await getDrinks(params)).items);
  };

  useEffect(() => { getFacets().then(setFacets).catch(()=>setFacets(null)); }, []);
  useEffect(() => { fetchData(); /* eslint-disable-next-line */ }, [q.toString()]);

  const setParam = (k: string, v?: string) => {
    const s = new URLSearchParams(q); v ? s.set(k, v) : s.delete(k); s.delete("page"); nav({ pathname: "/browse", search: s.toString() });
  };

  return (
    <div className="container" style={{ paddingTop: 16 }}>
      <h2>Browse</h2>
      <div className="row">
        <select value={q.get("spirit") || ""} onChange={(e)=>setParam("spirit", e.target.value || undefined)}>
          <option value="">All spirits</option>
          {facets && Object.keys(facets.spirits).sort().map(s => <option key={s} value={s}>{s} ({facets.spirits[s]})</option>)}
        </select>
        <select value={q.get("tag") || ""} onChange={(e)=>setParam("tag", e.target.value || undefined)}>
          <option value="">All tags</option>
          {facets && Object.keys(facets.tags).sort().map(t => <option key={t} value={t}>{t} ({facets.tags[t]})</option>)}
        </select>
        <select value={q.get("season") || ""} onChange={(e)=>setParam("season", e.target.value || undefined)}>
          <option value="">All seasons</option>
          {facets && Object.keys(facets.seasons).sort().map(s => <option key={s} value={s}>{s} ({facets.seasons[s]})</option>)}
        </select>
      </div>

      {!items && <div>Loading…</div>}
      {items && items.length === 0 && <div>No results.</div>}
      {items && items.length > 0 && <div className="grid">{items.map(d => <DrinkCard key={d.id} d={d} userId={user} />)}</div>}
    </div>
  );
}
