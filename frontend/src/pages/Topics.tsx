import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, friendlyError, TopicSummary } from "../api";
import { Icon } from "../ui/Icon";
import { Bar, ConfidenceMeter, Empty, ErrorState, OverviewSkeleton, StatusPill } from "../ui/kit";

/** Masked counts arrive as text ("fewer than 5"); show them smaller than real numbers. */
const statClass = (value: number | string) => typeof value === "string" ? "stat-value stat-text" : "stat-value";

export default function Topics() {
  const { id = "" } = useParams();
  const [data, setData] = useState<TopicSummary | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const load = () => { setError(""); return api.insights(id).then(setData).catch(error => setError(friendlyError(error))); };
  useEffect(() => { load(); }, [id]);
  const filtered = useMemo(() => data ? data.flagged.filter(topic => `${topic.name} ${topic.module || ""}`.toLowerCase().includes(search.toLowerCase())) : [], [data, search]);
  if (error) return <ErrorState message={error} retry={load} />;
  if (!data) return <OverviewSkeleton />;
  const { summary } = data;
  return <>
    <div className="page-head"><div><p className="eyebrow">Overview</p><h1>Topics</h1><p className="lead">Only topics where several students show confusion, backed by a second signal, appear here.</p></div></div>

    <section className="stats" aria-label="Course summary">
      <div className="stat"><div className="stat-label">Questions asked</div><div className={statClass(summary.questions)}>{summary.questions}</div></div>
      <div className="stat"><div className="stat-label">Students asked</div><div className={statClass(summary.students_asking)}>{summary.students_asking}<small> / {summary.enrolled}</small></div></div>
      <div className="stat"><div className="stat-label">Need attention</div><div className="stat-value" style={{ color: summary.needs_attention ? "var(--warn)" : undefined }}>{summary.needs_attention}<small> {summary.needs_attention === 1 ? "topic" : "topics"}</small></div></div>
    </section>

    <section className="section">
      <div className="section-head">
        <div><h2>Topics needing attention</h2><p className="note">Prioritised by signals from student questions and assessment results.</p></div>
        {data.flagged.length > 0 && <label className="search"><Icon name="search" /><input aria-label="Search topics" placeholder="Search topics" value={search} onChange={event => setSearch(event.target.value)} /></label>}
      </div>
      {data.flagged.length === 0 ? <Empty icon="spark" title="No topics need attention yet.">As students ask questions, topics appear here once the evidence is strong enough. Share the join code to get started.</Empty>
        : filtered.length === 0 ? <Empty icon="search" title="No topics match your search.">Try a different topic or module name.</Empty>
        : <div className="topic-grid">{filtered.map(topic => <article className="card topic-card" key={topic.id}>
          <div className="card-head"><div style={{ minWidth: 0 }}><h3 className="truncate" title={topic.name}>{topic.name}</h3><p className="card-meta truncate">{topic.module || "Course topic"}</p></div><StatusPill status={topic.status} /></div>
          <div><div className="share"><span className="share-value">{Math.round(topic.share * 100)}%</span><span className="share-label">of students show confusion</span></div>
            <div style={{ marginTop: 10 }}><Bar value={topic.share} label={`${Math.round(topic.share * 100)} percent of students`} /></div>
            <p className="note" style={{ marginTop: 8 }}>{`${topic.students_confused} students confused · ${topic.confusion_messages} questions`}</p></div>
          <div className="topic-foot"><ConfidenceMeter level={topic.confidence} /><Link className="btn btn-primary btn-sm" to={`/courses/${id}/topics/${topic.id}`}>Review evidence<Icon name="arrow" /></Link></div>
        </article>)}</div>}
    </section>

    {data.not_flagged.length > 0 && <section className="section">
      <div className="section-head"><div><h2>Being watched</h2><p className="note">Tangled keeps an eye on these. They'll move up if more students get stuck.</p></div></div>
      <div className="watch-list">{data.not_flagged.map(topic => <div className="watch-row" key={topic.id}><div style={{ minWidth: 0 }}><b className="truncate" style={{ display: "block" }}>{topic.name}</b><span className="note">{topic.reason}</span></div><span className="pill"><Icon name="eye" />Watching</span></div>)}</div>
    </section>}
  </>;
}
