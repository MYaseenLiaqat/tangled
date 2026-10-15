import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, friendlyError, TopicListItem } from "../api";

type FormValues = { name: string; module_label: string; description: string };

const emptyForm: FormValues = { name: "", module_label: "", description: "" };

export default function TopicsSetup() {
  const { id = "" } = useParams();
  const [topics, setTopics] = useState<TopicListItem[]>([]);
  const [form, setForm] = useState<FormValues>(emptyForm);
  const [editing, setEditing] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  async function load() {
    setLoading(true);
    try {
      setTopics(await api.topicList(id));
      setError("");
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [id]);

  function updateField(field: keyof FormValues, value: string) {
    setForm(current => ({ ...current, [field]: value }));
  }

  function startEdit(topic: TopicListItem) {
    setEditing(topic.id);
    setForm({ name: topic.name, module_label: topic.module_label, description: topic.description });
    setError("");
    setStatus("");
  }

  function cancelEdit() {
    setEditing(null);
    setForm(emptyForm);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setStatus("");
    try {
      if (editing === null) {
        await api.createTopic(id, form);
        setStatus("Topic added.");
      } else {
        await api.updateTopic(id, editing, form);
        setStatus("Topic updated.");
      }
      cancelEdit();
      await load();
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setSaving(false);
    }
  }

  async function remove(topic: TopicListItem) {
    if (!window.confirm(`Delete "${topic.name}"? This removes the topic association from related analysis data and indexed material tags.`)) return;
    setDeleting(topic.id);
    setError("");
    setStatus("");
    try {
      await api.deleteTopic(id, topic.id);
      if (editing === topic.id) cancelEdit();
      await load();
      setStatus(`Deleted ${topic.name}.`);
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setDeleting(null);
    }
  }

  return <main>
    <p><Link to={`/courses/${id}`}>Back to course</Link></p>
    <h1>Topics</h1>
    <p className="note">Set up the concepts your course tracks. {topics.length}/10 topics.</p>
    {error && <p className="error" role="alert">{error}</p>}
    <p className="success" aria-live="polite">{status}</p>
    <form className="panel form" onSubmit={submit}>
      <h2>{editing === null ? "Add a topic" : "Edit topic"}</h2>
      <input required placeholder="Topic name" value={form.name} onChange={event => updateField("name", event.target.value)} />
      <input required placeholder="Module label" value={form.module_label} onChange={event => updateField("module_label", event.target.value)} />
      <input required placeholder="One-sentence description" value={form.description} onChange={event => updateField("description", event.target.value)} />
      <div><button className="btn primary" disabled={saving || (editing === null && topics.length >= 10)}>{saving ? "Saving…" : editing === null ? "Add topic" : "Save changes"}</button>{editing !== null && <button type="button" className="btn" disabled={saving} onClick={cancelEdit}>Cancel</button>}</div>
    </form>
    {loading ? <div className="state"><p>Loading topics…</p></div> : topics.length === 0 ? <div className="empty panel">No topics yet.<small>Add the first topic above so Tangled can organise course questions.</small></div> :
      <div className="card-grid">{topics.map(topic => <article className="topic-card" key={topic.id}>
        <h3>{topic.name}</h3><p className="note">{topic.module_label}</p><p>{topic.description}</p>
        <button className="btn" disabled={saving || deleting === topic.id} onClick={() => startEdit(topic)}>Edit</button>{" "}
        <button className="btn" disabled={saving || deleting === topic.id} onClick={() => remove(topic)}>{deleting === topic.id ? "Deleting…" : "Delete"}</button>
      </article>)}</div>}
  </main>;
}
