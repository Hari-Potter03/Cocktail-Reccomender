import { useEffect, useState } from "react";
import { getProfile } from "../lib/api";
import { getUserId, getDisplayName } from "../lib/storage";
import type { ProfileResponse } from "../lib/types";

export default function Profile() {
  const user = getUserId() || "local";
  const [p, setP] = useState<ProfileResponse | null>(null);
  useEffect(() => { getProfile(user).then(setP).catch(()=>setP(null)); }, [user]);
  return (
    <div className="container" style={{ paddingTop: 16 }}>
      <h2>Profile {getDisplayName() ? `— ${getDisplayName()}` : ""}</h2>
      {!p && <div>Loading…</div>}
      {p && (
        <div>
          <p>Ratings: {p.ratings_count} • Personalized: {p.has_taste ? "Yes" : "No"}</p>
          <div className="row">
            {p.summary?.primary_spirit && <span className="badge">primary: {p.summary.primary_spirit}</span>}
            {(p.summary?.top_tags || []).map(t => <span key={t} className="badge">{t}</span>)}
            {(p.summary?.top_seasons || []).map(s => <span key={s} className="badge">{s}</span>)}
          </div>
        </div>
      )}
    </div>
  );
}
