import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, friendlyError, TopicSummary } from "../api";

export default function Topics() {
  const { id = "" } = useParams();
  const [data, setData] = useState<TopicSummary | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const load = () => api.insights(id).then(setData).catch(error => setError(friendlyError(error)));
  useEffect(() => { load(); }, [id]);
  const filtered = useMemo(() => data ? data.flagged.filter(topic => `${topic.name} ${topic.module || ""}`.toLowerCase().includes(search.toLowerCase())) : [], [data, search]);
  if (error) return <PageState message={error} retry={load} />;
  if (!data) return <PageState message="Loading topics…" />;
  return <><h1>Topics</h1><p className="note">Only topics with several students showing confusion appear here.</p>
    <section className="summary"><div><b>{data.summary.questions}</b><span>questions asked</span></div><div><b>{data.summary.students_asking} of {data.summary.enrolled}</b><span>students asked</span></div><div><b>{data.summary.needs_attention}</b><span>topics need attention</span></div></section>
    <div className="section-toolbar"><div><h2 className="section-title">Topics needing attention</h2><p className="note">Prioritised by signals from student questions and assessment results.</p></div><label className="search"><span>⌕</span><input aria-label="Search topics" placeholder="Search topics" value={search} onChange={event => setSearch(event.target.value)} /></label></div>
    {data.flagged.length === 0 ? <div className="empty panel">No topics need attention yet.<small>As students ask questions, topics will appear here when the evidence is strong enough.</small></div> : filtered.length === 0 ? <div className="empty panel">No topics match your search.<small>Try a different topic or module name.</small></div> :
      <div className="card-grid">{filtered.map(topic => <article className="topic-card" key={topic.id}>
        <div className="card-head"><div><h3>{topic.name}</h3><small>{topic.module || "Course topic"}</small></div><span className={`tag ${topic.status === "addressed" ? "addressed" : "review"}`}>{topic.status === "addressed" ? "Addressed" : "Review"}</span></div>
        <div className="percentage"><strong>{Math.round(topic.share * 100)}%</strong><span>of students show confusion</span></div><div className="bar" aria-label={`${Math.round(topic.share * 100)} percent of students`}><i style={{ width: `${Math.min(topic.share * 100, 100)}%` }} /></div>
        <div className="card-foot"><span className={`tag ${topic.confidence === "High" ? "addressed" : "monitor"}`}>{topic.confidence || "Pending"} confidence</span><Link className="btn primary" to={`/courses/${id}/topics/${topic.id}`}>View details <span aria-hidden="true">→</span></Link></div>
      </article>)}</div>}
  </>;
}

function PageState({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="state" role={retry ? "alert" : undefined}><p>{message}</p>{retry && <button className="btn" onClick={retry}>Try again</button>}</div>;
}
