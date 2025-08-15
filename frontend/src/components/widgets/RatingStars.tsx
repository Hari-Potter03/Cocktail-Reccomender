import { useState } from "react";
import { postRating } from "../../lib/api";

export default function RatingStars({ drinkId, userId, onRated }: { drinkId: string; userId: string; onRated?: () => void }) {
  const [val, setVal] = useState(0);
  const [busy, setBusy] = useState(false);
  const submit = async (v: number) => {
    try {
      setBusy(true);
      setVal(v);
      await postRating({ user_id: userId || "local", drink_id: drinkId, rating: v, tried: true });
      onRated?.();
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="row" aria-label="rate">
      {[1,2,3,4,5].map(n => (
        <button key={n} disabled={busy} onClick={() => submit(n)} style={{ background:"transparent", border:"none", cursor:"pointer", fontSize:18 }}>
          {n <= val ? "★" : "☆"}
        </button>
      ))}
    </div>
  );
}
