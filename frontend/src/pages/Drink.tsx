import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getDrink, getSimilar } from "../lib/api";
import type { Drink, DrinkCard } from "../lib/types";
import DrinkCardComp from "../components/cards/DrinkCard";
import RatingStars from "../components/widgets/RatingStars";
import { getUserId } from "../lib/storage";

export default function Drink() {
  const { id = "" } = useParams();
  const [drink, setDrink] = useState<Drink | null>(null);
  const [sim, setSim] = useState<DrinkCard[]>([]);
  const user = getUserId() || "local";

  useEffect(() => {
    setDrink(null); setSim([]);
    getDrink(id).then(setDrink);
    getSimilar(id, 12).then(r => setSim(r.items));
  }, [id]);

  if (!drink) return <div className="container" style={{ paddingTop: 16 }}>Loading…</div>;

  return (
    <div className="container" style={{ paddingTop: 16 }}>
      <div className="row">
        <img src={drink.image_url || ""} alt={drink.name} style={{ width: 320, borderRadius: 12 }} />
        <div style={{ marginLeft: 16, maxWidth: 700 }}>
          <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ margin: 0 }}>{drink.name}</h2>
            <RatingStars drinkId={drink.id} userId={user} withTried showLabel />
          </div>

          <div className="row" style={{ margin: "8px 0" }}>
            {drink.primary_spirit && <span className="badge">{drink.primary_spirit}</span>}
            {(drink.tags || []).map(t => <span key={t} className="badge">{t}</span>)}
            {(drink.season || []).map(s => <span key={s} className="badge">{s}</span>)}
          </div>

          <h4>Ingredients</h4>
          <ul>{(drink.ingredients || []).map((ing, i) => <li key={i}>{ing}</li>)}</ul>
          {drink.technique && <p><b>Technique:</b> {drink.technique}</p>}
        </div>
      </div>

      <div className="space" />
      <h3>Similar</h3>
      <div className="grid">{sim.map(d => <DrinkCardComp key={d.id} d={d} userId={user} />)}</div>
    </div>
  );
}
