import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";

export default function TopicsSetup() {
  const { id = "" } = useParams();
  const [topics, setTopics] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [moduleLabel, setModuleLabel] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const load = () => api.topicsForCourse(id).then(setTopics).catch(err => setError(String(err)));
  useEffect(() => { load(); }, [id]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await api.createTopic(id, { name, module_label: moduleLabel, description });
      setName(""); setModuleLabel(""); setDescription(""); setError(""); load();
    } catch (err) { setError(String(err)); }
  }
  return <main><p><Link to={`/courses/${id}`}>Back to course</Link></p><h1>Topics</h1>
    <p className="mute">Set up the concepts your course tracks. {topics.length}/10 topics.</p>
    <form className="panel" onSubmit={submit}>
      <input required placeholder="Topic name" value={name} onChange={e => setName(e.target.value)} />
      <input required placeholder="Module label" value={moduleLabel} onChange={e => setModuleLabel(e.target.value)} />
      <input required placeholder="One-sentence description" value={description} onChange={e => setDescription(e.target.value)} />
      <button className="btn p" disabled={topics.length >= 10}>Add topic</button>
      {error && <p className="bad">{error}</p>}
    </form>
    <div className="grid2">{topics.map(topic => <div className="card pad" key={topic.id}><h3>{topic.name}</h3><p className="mute">{topic.module_label}</p><p>{topic.description}</p>
      <button className="btn" onClick={async () => { await api.deleteTopic(id, topic.id); load(); }}>Delete</button>
    </div>)}</div>
  </main>;
}
