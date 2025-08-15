import { Link } from "react-router-dom";
import type { DrinkCard as Card } from "../../lib/types";
import ReasonChips from "../widgets/ReasonChips";
import RatingStars from "../widgets/RatingStars";

export default function DrinkCard({ d, onRated, userId }: { d: Card; onRated?: () => void; userId: string }) {
  return (
    <div className="card">
      <Link to={`/drink/${d.id}`}><img src={d.image_url || ""} alt={d.name} /></Link>
      <div style={{ padding: 12 }}>
        <div style={{ fontWeight: 700, marginBottom: 6 }}>{d.name}</div>
        <div className="row">
          {d.primary_spirit && <span className="badge">{d.primary_spirit}</span>}
          {(d.tags || []).slice(0, 2).map(t => <span key={t} className="badge">{t}</span>)}
        </div>
        {d.reason && d.reason.length > 0 && <ReasonChips reason={d.reason} />}

        <div className="row" style={{ justifyContent: "space-between", marginTop: 10 }}>
          <Link className="button" to={`/drink/${d.id}`}>Details</Link>
          <RatingStars drinkId={d.id} userId={userId} onRated={onRated} showLabel />
        </div>
      </div>
    </div>
  );
}
