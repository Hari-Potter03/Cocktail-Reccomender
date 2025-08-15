import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAgeOk, setAgeOk, setDisplayName, setUserId } from "../lib/storage";

// Safer ID generator with fallbacks
const makeId = () => {
  const c: any = globalThis.crypto as any;
  if (c?.randomUUID) return c.randomUUID();
  if (c?.getRandomValues) {
    const b = new Uint8Array(16);
    c.getRandomValues(b);
    b[6] = (b[6] & 0x0f) | 0x40; // version 4
    b[8] = (b[8] & 0x3f) | 0x80; // variant
    const h = Array.from(b, n => n.toString(16).padStart(2, "0")).join("");
    return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`;
  }
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
};

export default function Login() {
  const [name, setName] = useState("");
  const [age, setAge] = useState(getAgeOk());
  const nav = useNavigate();

  const submit = () => {
    if (!age) { alert("Please confirm you're of legal drinking age."); return; }
    const uid = makeId();
    setUserId(uid);
    setDisplayName(name || "Guest");
    setAgeOk(true);
    nav("/onboarding");  // will work once App.tsx re-checks auth on nav
  };

  return (
    <div className="container" style={{ paddingTop: 40 }}>
      <h2>Welcome</h2>
      <p>Sign in locally (no server auth needed).</p>
      <div className="row">
        <input
          className="input"
          placeholder="Display name"
          value={name}
          onChange={e => setName(e.target.value)}
        />
      </div>
      <div className="row" style={{ marginTop: 10 }}>
        <label>
          <input
            type="checkbox"
            checked={age}
            onChange={(e)=>setAge(e.target.checked)}
          />{" "}
          I am of legal drinking age.
        </label>
      </div>
      <div className="space" />
      <button className="button primary" onClick={submit}>Continue</button>
    </div>
  );
}
