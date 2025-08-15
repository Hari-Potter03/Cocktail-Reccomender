import { useState } from "react";
import { postRating } from "../../lib/api";

export default function RatingStars({
  drinkId,
  userId,
  onRated,
  withTried = false,
  showLabel = true,
}: {
  drinkId: string;
  userId: string;
  onRated?: () => void;
  withTried?: boolean;
  showLabel?: boolean;
}) {
  const [val, setVal] = useState(0);
  const [hover, setHover] = useState(0);
  const [busy, setBusy] = useState(false);
  const [tried, setTried] = useState(true);
  const stars = [1, 2, 3, 4, 5];

  const submit = async (v: number) => {
    if (!userId) { alert("Please login first."); return; }
    try {
      setBusy(true);
      setVal(v);
      await postRating({ user_id: userId, drink_id: drinkId, rating: v, tried });
      onRated?.();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="row" style={{ alignItems: "center", gap: 8 }}>
      {showLabel && <span style={{ fontSize: 13, opacity: 0.8 }}>Rate:</span>}
      {stars.map((n) => (
        <button
          key={n}
          disabled={busy}
          onMouseEnter={() => setHover(n)}
          onMouseLeave={() => setHover(0)}
          onClick={() => submit(n)}
          title={`${n} star${n > 1 ? "s" : ""}`}
          style={{
            background: "transparent",
            border: "none",
            cursor: "pointer",
            fontSize: 22,
            lineHeight: 1,
            color: n <= (hover || val) ? "#ffd166" : "#6b7280",
            padding: 0,
          }}
          aria-label={`${n} star`}
        >
          ★
        </button>
      ))}
      {withTried && (
        <label style={{ marginLeft: 8, fontSize: 13, opacity: 0.9 }}>
          <input type="checkbox" checked={tried} onChange={(e) => setTried(e.target.checked)} /> Tried
        </label>
      )}
    </div>
  );
}
