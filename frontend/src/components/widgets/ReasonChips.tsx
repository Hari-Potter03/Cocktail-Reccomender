export default function ReasonChips({ reason }: { reason: string[] }) {
  return (
    <div className="row" style={{ marginTop: 8 }}>
      {reason.slice(0,3).map((r, i) => <span key={i} className="badge">{r}</span>)}
    </div>
  );
}
