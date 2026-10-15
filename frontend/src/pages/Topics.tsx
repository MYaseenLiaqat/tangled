import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, friendlyError, TopicSummary } from "../api";

export default function Topics() {
  const { id = "" } = useParams();
  const [data, setData] = useState<TopicSummary | null>(null);
  const [error, setError] = useState("");
  const load = () => api.insights(id).then(setData).catch(error => setError(friendlyError(error)));
  useEffect(() => { load(); }, [id]);
  if (error) return <PageState message={error} retry={load} />;
  if (!data) return <PageState message="Loading topics…" />;
  return <><h1>Topics</h1><p className="note">Only topics with several students showing confusion appear here.</p>
    <section className="summary"><div><b>{data.summary.questions}</b>questions asked</div><div><b>{data.summary.students_asking} of {data.summary.enrolled}</b>students asked</div><div><b>{data.summary.needs_attention}</b>topics need attention</div></section>
    <h2 className="section-title">Topics needing attention</h2>
    {data.flagged.length === 0 ? <div className="empty panel">No topics need attention yet.<small>As students ask questions, topics will appear here when the evidence is strong enough.</small></div> :
      <div className="card-grid">{data.flagged.map(topic => <article className="topic-card" key={topic.id}>
        <div className="card-head"><div><h3>{topic.name}</h3><small>{topic.module}</small></div><span className={`tag ${topic.status === "addressed" ? "ok" : "review"}`}>{topic.status === "addressed" ? "Addressed" : "Needs attention"}</span></div>
        <div className="percentage"><strong>{Math.round(topic.share * 100)}%</strong><span>of students show confusion</span></div><div className="bar" aria-label={`${Math.round(topic.share * 100)} percent of students`}><i style={{ width: `${Math.min(topic.share * 100, 100)}%` }} /></div>
        <div className="card-foot"><span className={`tag ${topic.confidence === "High" ? "ok" : "monitor"}`}>{topic.confidence} confidence</span><Link className="btn primary" to={`/courses/${id}/topics/${topic.id}`}>View details</Link></div>
      </article>)}</div>}
  </>;
}

function PageState({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="state" role={retry ? "alert" : undefined}><p>{message}</p>{retry && <button className="btn" onClick={retry}>Try again</button>}</div>;
}
