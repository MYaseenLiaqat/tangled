import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Topics() {
  const [d, setD] = useState<any>(null);
  useEffect(() => { api.topics().then(setD); }, []);
  if (!d) return <p className="mute">Loading…</p>;
  const s = d.summary;
  return (<>
    <h1>Topics</h1>
    <div className="kpi"><div><b>{s.questions}</b>questions asked</div><div><b>{s.students_asking} of {s.enrolled}</b>students asked a question</div><div><b>{s.needs_attention}</b>topics need attention</div></div>
    <h2>Topics needing attention</h2><p className="mute">Shown only when several students show confusion and a second signal agrees.</p>
    {d.flagged.length === 0 && <div className="panel">No topics need attention right now.</div>}
    <div className="grid2">{d.flagged.map((t: any) => (
      <div className="card" key={t.id}>
        <div className="ch"><div><h3>{t.name}</h3><div className="mute">{t.module}</div></div>
          <span className={"tag " + (t.status === "addressed" ? "ok" : "rev")}>{t.status === "addressed" ? "Addressed" : "Needs attention"}</span></div>
        <div className="pad"><div className="mute"><b className="big">{Math.round(t.share * 100)}%</b> of students show confusion</div>
          <div className="bar lg"><i style={{ width: t.share * 100 + "%" }} /></div>
          <span className={"tag " + (t.confidence === "High" ? "ok" : "mon")}>{t.confidence} confidence</span>
          <div style={{ marginTop: 20 }}><Link className="btn p" to={`/teacher/topics/${t.id}`}>View details</Link></div></div>
      </div>))}</div>
    {d.not_flagged.map((n: any) => <p className="note" key={n.name}>Not flagged: {n.name}. {n.reason}</p>)}
  </>);
}
