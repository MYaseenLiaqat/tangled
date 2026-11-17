import { FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, Course, friendlyError, TopicListItem } from "../api";

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
  const [course, setCourse] = useState<Course | null>(null);
  const [courseName, setCourseName] = useState("");
  const [classSize, setClassSize] = useState("");
  const [courseSaving, setCourseSaving] = useState(false);

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
  useEffect(() => {
    api.course(id).then(value => {
      setCourse(value);
      setCourseName(value.name);
      setClassSize(value.class_size ? String(value.class_size) : "");
    }).catch(err => setError(friendlyError(err)));
  }, [id]);

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

  async function saveCourse(event: FormEvent) {
      event.preventDefault();
      setCourseSaving(true);
      setError("");
      setStatus("");
      try {
        const updated = await api.updateCourse(id, {
          name: courseName,
          class_size: classSize ? Number(classSize) : null,
          joining_open: course?.joining_open ?? true,
        });
        setCourse(updated);
        setStatus("Course settings saved.");
      } catch (err) {
        setError(friendlyError(err));
      } finally {
        setCourseSaving(false);
      }
    }

  async function regenerateCode() {
      if (!window.confirm("Generate a new join code? Existing links will stop working.")) return;
      setCourseSaving(true);
      setError("");
      try {
        setCourse(await api.regenerateCode(id));
        setStatus("Join code regenerated.");
      } catch (err) {
        setError(friendlyError(err));
      } finally {
        setCourseSaving(false);
      }
    }

  async function deleteCourse() {
      if (!course || !window.confirm(`Delete "${course.name}" and all of its data?`)) return;
      const confirmation = window.prompt(`Type "${course.name}" to confirm deletion.`);
      if (confirmation === null) return;
      setCourseSaving(true);
      setError("");
      try {
        await api.deleteCourse(id, confirmation);
        window.location.assign("/courses");
      } catch (err) {
        setError(friendlyError(err));
        setCourseSaving(false);
      } finally {
        setCourseSaving(false);
      }
    }

  return <main>
    <p><Link to={`/courses/${id}`}>Back to course</Link></p>
    <h1>Topics</h1>
    <p className="note">Set up the concepts your course tracks. {topics.length}/10 topics.</p>
    {error && <p className="error" role="alert">{error}</p>}
    <p className="success" aria-live="polite">{status}</p>
    {course && <section className="panel">
      <h2>Course settings</h2>
      <form className="form" onSubmit={saveCourse}>
        <label>Course name<input required value={courseName} onChange={event => setCourseName(event.target.value)} /></label>
        <label>Class size (optional)<input type="number" min="1" value={classSize} onChange={event => setClassSize(event.target.value)} /></label>
        <label><input type="checkbox" checked={course.joining_open} onChange={event => setCourse(current => current ? { ...current, joining_open: event.target.checked } : current)} /> Allow new students to join</label>
        <div><button className="btn primary" disabled={courseSaving}>{courseSaving ? "Saving…" : "Save settings"}</button>{" "}
          <button type="button" className="btn" disabled={courseSaving} onClick={regenerateCode}>Regenerate join code</button></div>
      </form>
      <p className="note">Current join code: <b>{course.join_code}</b> · Share link: <code>{course.join_link}</code></p>
      <button type="button" className="btn danger" disabled={courseSaving} onClick={deleteCourse}>Delete course</button>
    </section>}
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
