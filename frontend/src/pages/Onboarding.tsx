import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { setOnboarding, getUserId } from "../lib/storage";
import { postRecs } from "../lib/api";

const SPIRITS = ["tequila","gin","vodka","rum","whiskey","bourbon","scotch","mezcal","brandy"];
const TAGS = ["citrusy","herbal","fruity","sweet","spicy","bitter","creamy","smoky"];
const SEASONS = ["spring","summer","fall","winter"];

function ToggleGroup({ options, selected, onChange }: { options:string[]; selected:Set<string>; onChange:(v:Set<string>)=>void }) {
  return (
    <div className="row">
      {options.map(o => (
        <button key={o} className={`badge`} style={{ textTransform:"capitalize", background: selected.has(o) ? "#243b4a" : "#1f2937" }}
          onClick={(e)=>{ e.preventDefault(); const s = new Set(selected); s.has(o) ? s.delete(o) : s.add(o); onChange(s); }}>
          {o}
        </button>
      ))}
    </div>
  );
}

export default function Onboarding() {
  const nav = useNavigate();
  const [spirit, setSpirit] = useState<Set<string>>(new Set());
  const [like, setLike] = useState<Set<string>>(new Set());
  const [avoid, setAvoid] = useState<Set<string>>(new Set());
  const [season, setSeason] = useState<string | null>(null);

  const submit = async () => {
    const user_id = getUserId() || "local";
    const payload = {
      user_id,
      likes: { spirit: [...spirit], tags: [...like], season: season ? [season] : [] },
      dislikes: { tags: [...avoid] },
      k: 24,
    };
    setOnboarding({ spirit: [...spirit], tags: [...like], season: season ? [season] : [], avoid_tags: [...avoid] });
    // Warm the first recs (ignore response here)
    try { await postRecs(payload); } catch {}
    nav("/");
  };

  return (
    <div className="container" style={{ paddingTop: 24 }}>
      <h2>Tell us your tastes</h2>
      <p>Pick a few that apply (you can change later).</p>

      <h4>Spirits</h4>
      <ToggleGroup options={SPIRITS} selected={spirit} onChange={setSpirit} />

      <h4 style={{ marginTop: 12 }}>Like these flavors</h4>
      <ToggleGroup options={TAGS} selected={like} onChange={setLike} />

      <h4 style={{ marginTop: 12 }}>Avoid these</h4>
      <ToggleGroup options={TAGS} selected={avoid} onChange={setAvoid} />

      <h4 style={{ marginTop: 12 }}>Season</h4>
      <div className="row">
        {SEASONS.map(s => (
          <button key={s} className="badge" style={{ textTransform:"capitalize", background: season===s ? "#243b4a" : "#1f2937" }} onClick={(e)=>{ e.preventDefault(); setSeason(season===s?null:s); }}>{s}</button>
        ))}
      </div>

      <div className="space" />
      <button className="button primary" onClick={submit}>See my picks</button>
    </div>
  );
}
