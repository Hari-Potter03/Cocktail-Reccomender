import { NavLink } from "react-router-dom";
const spirits = ["tequila","gin","vodka","rum","whiskey","bourbon","scotch","mezcal","brandy"];
export default function SpiritTabs() {
  return (
    <div className="row" style={{ overflowX:"auto", padding: "0 0 12px 0" }}>
      {spirits.map(s => (
        <NavLink key={s} to={`/browse?spirit=${s}`} className="badge" style={{ textTransform:"capitalize" }}>{s}</NavLink>
      ))}
    </div>
  );
}
