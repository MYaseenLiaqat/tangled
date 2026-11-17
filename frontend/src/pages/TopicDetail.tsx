import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, friendlyError, TopicDetail as Detail } from "../api";
import { Icon } from "../ui/Icon";
import { ConfidenceMeter, Empty, ErrorState, ListSkeleton, StatusPill } from "../ui/kit";

/** Marks the whole clause that carries the confusion wording, so a highlight never cuts a word in half. */
function Highlight({ text }: { text: string }) {
  const match = text.match(/[^.!?;]*\b(confus|understand|unclear|mistake|wrong|lost|struggl|don't get|do not get|stuck)\w*[^.!?;]*/i);
  if (!match || match.index === undefined) return <>{text}</>;
  const start = match.index + (match[0].length - match[0].trimStart().length);
  const clause = match[0].trim();
  return <>{text.slice(0, start)}<mark>{clause}</mark>{text.slice(start + clause.length)}</>;
}

export default function TopicDetail() {
  const { id = "", topicId = "" } = useParams();
  const [data, setData] = useState<Detail | null>(null); const [error, setError] = useState(""); const [busy, setBusy] = useState(false); const [status, setStatus] = useState("");
  const load = () => { setError(""); return api.topic(id, topicId).then(setData).catch(error => setError(friendlyError(error))); };
  useEffect(() => { load(); }, [id, topicId]);
  async function mark(verdict: "addressed" | "false_alarm") { setBusy(true); setStatus(""); try { await api.verdict(id, Number(topicId), verdict); setStatus(verdict === "addressed" ? "Marked as addressed." : "Marked as not a real problem."); load(); } catch (error) { setStatus(friendlyError(error)); } finally { setBusy(false); } }
  if (error) return <ErrorState message={error} retry={load} />;
  if (!data) return <><Link className="back-link" to={`/courses/${id}/topics`}><Icon name="back" />All topics</Link><ListSkeleton rows={3} height={120} label="Loading topic details…" /></>;
  const stats = data.stats;
  const flagged = data.tier === "needs_attention";
  return <>
    <Link className="back-link" to={`/courses/${id}/topics`}><Icon name="back" />All topics</Link>
    <div className="detail-head"><div style={{ minWidth: 0 }}><p className="eyebrow">Topic evidence</p><h1 className="clamp-2">{data.name}</h1><p className="lead">{data.module || "Course topic"}</p></div><StatusPill status={data.status === "addressed" ? "addressed" : flagged ? "review" : "watch"} /></div>
    <div className="facts">
      <span className="fact">Share <b>{Math.round(data.share * 100)}%</b></span>
      <span className="fact">Confusion questions <b>{stats.confusion_msgs}</b></span>
      <span className="fact"><ConfidenceMeter level={data.confidence} /></span>
    </div>

    <section className="section">
      <div className="section-head"><div><h2>Why Tangled flagged this</h2><p className="note">Independent signals that agree this topic needs attention.</p></div></div>
      <div className="card signal-list">{data.signals.length ? data.signals.map(signal => <div className="signal" key={signal}><span className="signal-icon"><Icon name="check" /></span><span style={{ textTransform: "none" }}>{signal.charAt(0).toUpperCase() + signal.slice(1)}</span></div>)
        : <div className="signal"><span className="signal-icon" style={{ background: "var(--surface-sunken)", color: "var(--mute)" }}><Icon name="info" /></span>No corroborating signals yet.</div>}</div>
    </section>

    <section className="section">
      <div className="section-head"><div><h2>What students are confused about</h2><p className="note">Questions classified as confusion, grouped by meaning. Highlights mark the evidence phrase.</p></div></div>
      {data.groups.length ? data.groups.map(group => <article className="card group-card" key={group.title}>
        <div className="card-head"><h3 className="clamp-2">{group.title}</h3><span className="pill">{`${group.count} questions`}</span></div>
        {group.evidence_phrases.map(phrase => <p className="quote" key={phrase}>“<Highlight text={phrase} />”</p>)}
      </article>) : <Empty icon="message" title="Not enough data yet.">Groups appear once a few students describe what confuses them.</Empty>}
    </section>

    {data.not_counted_evidence.length > 0 && <section className="section"><details className="card"><summary>Not counted: information questions <span className="pill pill-info">{`${data.not_counted_evidence.length} shown`}</span></summary>{data.not_counted_evidence.map(item => <p className="quote" key={item}>{item}</p>)}</details></section>}

    <div className="action-bar"><button className="btn btn-primary" disabled={busy} onClick={() => mark("addressed")}><Icon name="check" />Mark as addressed</button><button className="btn btn-ghost" disabled={busy} onClick={() => mark("false_alarm")}>Not a real problem</button><span aria-live="polite">{status}</span></div>
  </>;
}
