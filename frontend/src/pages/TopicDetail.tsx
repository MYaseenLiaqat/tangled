import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

function Highlight({ text, phrase }: { text: string; phrase: string }) {
  const i = phrase ? text.indexOf(phrase) : -1;
  if (i < 0) return <>{text}</>;
  return <>{text.slice(0, i)}<mark>{phrase}</mark>{text.slice(i + phrase.length)}</>;
}

export default function TopicDetail() {
  const { id } = useParams(); const nav = useNavigate();
  const [d, setD] = useState<any>(null);
  const load = () => api.topic(id!).then(setD);
  useEffect(() => { load(); }, [id]);
  if (!d) return <p className="mute">Loading…</p>;
  const total = d.stats.confusion_msgs || 1;
  return (<>
    <Link className="btn back" to="/teacher">← All topics</Link>
    <div className="hd"><div><h1>{d.name}</h1><div className="mute">{d.module}</div></div>{d.confidence && <span className="tag ok">{d.confidence} confidence</span>}</div>
    <h2>Why Tangled flagged this</h2><p className="mute">Checks that must pass before a topic is shown to you.</p>
    <div className="panel">{d.checks.map((c: any, i: number) => <div className="chk" key={i}><i className={c.ok ? "" : "no"}>{c.ok ? "✓" : "–"}</i><span>{c.text}</span></div>)}</div>
    <h2>What students are confused about</h2><p className="mute">Only questions classified as confusion. The highlight marks the words that show it.</p>
    {d.groups.map((g: any, i: number) => (
      <div className="card" key={i}><div className="ch"><h3>{g.title}</h3><span className="mute">{g.count} questions</span></div>
        <div className="bar" style={{ margin: "0 22px" }}><i style={{ width: (g.count / total) * 100 + "%" }} /></div>
        <ul>{g.items.map((m: any) => <li key={m.id}>“<Highlight text={m.text} phrase={m.phrase} />”{m.misconception && <span className="rs">Misconception</span>}</li>)}</ul></div>))}
    {d.excluded.length > 0 && <details className="panel"><summary>Not counted: {d.stats.info_msgs} questions that only asked for information</summary><ul>{d.excluded.map((x: string, i: number) => <li key={i}>“{x}”</li>)}</ul></details>}
    <p className="note">Misconception means the student’s own statement conflicts with your course material.</p>
    <button className="btn p" onClick={() => api.verdict(d.id, "addressed").then(load)}>Mark as addressed</button>{" "}
    <button className="btn" onClick={() => api.verdict(d.id, "false_alarm").then(() => nav("/teacher"))}>Not a real problem</button>
  </>);
}
