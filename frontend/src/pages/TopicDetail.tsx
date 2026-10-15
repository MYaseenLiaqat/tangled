import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, friendlyError, TopicDetail as Detail } from "../api";

function Highlight({ text }: { text: string }) {
  const match = text.match(/(.{0,45}\b(confus|understand|unclear|mistake|wrong)\w*.{0,70})/i);
  if (!match) return <>{text}</>;
  return <>{text.slice(0, match.index)}<mark>{match[1]}</mark>{text.slice((match.index || 0) + match[1].length)}</>;
}

export default function TopicDetail() {
  const { id = "", topicId = "" } = useParams();
  const [data, setData] = useState<Detail | null>(null); const [error, setError] = useState(""); const [busy, setBusy] = useState(false); const [status, setStatus] = useState("");
  const load = () => api.topic(id, topicId).then(setData).catch(error => setError(friendlyError(error)));
  useEffect(() => { load(); }, [id, topicId]);
  async function mark(verdict: "addressed" | "false_alarm") { setBusy(true); setStatus(""); try { await api.verdict(id, Number(topicId), verdict); setStatus(verdict === "addressed" ? "Marked as addressed." : "Marked as not a real problem."); load(); } catch (error) { setStatus(friendlyError(error)); } finally { setBusy(false); } }
  if (error) return <div className="state" role="alert"><p>{error}</p><button className="btn" onClick={load}>Try again</button></div>;
  if (!data) return <div className="state"><p>Loading topic details…</p></div>;
  const stats = data.stats;
  return <><Link className="back" to={`/courses/${id}/topics`}>← All topics</Link><div className="detail-head"><div><h1>{data.name}</h1><p className="note">{data.module}</p></div>{data.confidence && <span className="tag">{data.confidence} confidence</span>}</div>
    <h2>Why Tangled flagged this</h2><p className="note">These signals agree that this topic needs attention.</p><div className="panel checks">{data.signals.length ? data.signals.map(signal => <p key={signal}><b>✓</b>{signal}</p>) : <p>No corroborating signals.</p>}</div>
    <h2>Confusion groups</h2>{data.groups.length ? data.groups.map(group => <article className="group panel" key={group.title}><div className="card-head"><h3>{group.title}</h3><small>{group.count} questions</small></div>{group.evidence_phrases.map(phrase => <p key={phrase}>“<Highlight text={phrase} />”</p>)}<span className="pill">Misconception signal where identified</span></article>) : <div className="empty panel">Not enough data yet.</div>}
    {data.not_counted_evidence.length > 0 && <details className="panel"><summary>Not counted: information questions</summary>{data.not_counted_evidence.map(item => <p className="note" key={item}>{item}</p>)}</details>}
    <div className="facts"><span>Share <b>{Math.round(data.share * 100)}%</b></span><span>Confusion messages <b>{stats.confusion_msgs}</b></span></div>
    <div className="actions"><button className="btn primary" disabled={busy} onClick={() => mark("addressed")}>Mark as addressed</button><button className="btn" disabled={busy} onClick={() => mark("false_alarm")}>Not a real problem</button><span aria-live="polite">{status}</span></div>
  </>;
}
