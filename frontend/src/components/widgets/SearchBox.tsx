import { useState } from "react";

export default function SearchBox({ onSubmit }: { onSubmit: (q: string) => void }) {
  const [q, setQ] = useState("");
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(q.trim()); }}>
      <input className="input" placeholder="Search drinks or ingredients..." value={q} onChange={(e) => setQ(e.target.value)} style={{ width: 400 }} />
    </form>
  );
}
