import { Link, NavLink, useNavigate } from "react-router-dom";
import SearchBox from "../widgets/SearchBox";
import SpiritTabs from "../widgets/SpiritTabs";
import { getUserId } from "../../lib/storage";

export default function Navbar() {
  const navigate = useNavigate();
  const authed = !!getUserId();

  const handleSearch = (q: string) => {
    const qs = q.trim();
    if (!qs) return;
    navigate(`/browse?q=${encodeURIComponent(qs)}`);
  };

  const logout = () => {
    ["cr_user_id","cr_display_name","cr_onboarding","cr_age_ok"].forEach(k => localStorage.removeItem(k));
    navigate("/login");
  };

  return (
    <div className="nav">
      <div className="container row" style={{ justifyContent: "space-between", padding: 12 }}>
        <div className="row" style={{ gap: 16 }}>
          <Link to="/" style={{ fontWeight: 800, letterSpacing: 0.3, fontSize: 18 }}>🍹 Cocktail Recs</Link>
          <NavLink to="/browse" className="badge">Browse</NavLink>
        </div>

        <div className="row" style={{ flex: 1, maxWidth: 700 }}>
          <SearchBox onSubmit={handleSearch} />
        </div>

        <div className="row" style={{ gap: 8 }}>
          <NavLink to="/profile" className="badge">Profile</NavLink>
          {authed
            ? <button className="badge" onClick={logout} style={{ cursor:"pointer", background:"#2a3240" }}>Logout</button>
            : <NavLink to="/login" className="badge">Login</NavLink>}
        </div>
      </div>
      <div className="container" style={{ paddingBottom: 12 }}>
        <SpiritTabs />
      </div>
    </div>
  );
}
