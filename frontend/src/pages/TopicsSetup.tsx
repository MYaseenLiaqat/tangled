import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, Course, friendlyError, TopicListItem } from "../api";
import { Icon } from "../ui/Icon";
import { Bar, ConfirmDialog, CopyButton, Empty, ListSkeleton, Toast } from "../ui/kit";

type FormValues = { name: string; module_label: string; description: string };
type Pending = { kind: "topic"; topic: TopicListItem } | { kind: "regenerate" } | { kind: "course" } | null;

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
  const [pending, setPending] = useState<Pending>(null);

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

  async function deleteCourse(confirmation: string) {
    if (!course) return;
    setCourseSaving(true);
    setError("");
    try {
      await api.deleteCourse(id, confirmation);
      window.location.assign("/courses");
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setCourseSaving(false);
    }
  }

  function confirmPending(typed: string) {
    const action = pending;
    setPending(null);
    if (action?.kind === "topic") remove(action.topic);
    if (action?.kind === "regenerate") regenerateCode();
    if (action?.kind === "course") deleteCourse(typed);
  }

  const full = editing === null && topics.length >= 10;
  const joinUrl = course ? `${window.location.origin}${course.join_link}` : "";

  return <>
    <div className="page-head"><div><p className="eyebrow">Setup</p><h1>Topic setup</h1><p className="lead">Set up the concepts your course tracks, and how students join.</p></div></div>
    {error && <p className="alert" role="alert" style={{ marginBottom: 16 }}><Icon name="alert" />{error}</p>}

    <div className="setup-grid">
      <div style={{ display: "grid", gap: 20, minWidth: 0 }}>
        <section className="card">
          <div className="card-head" style={{ padding: "18px 20px", borderBottom: "1px solid var(--line)", alignItems: "center" }}>
            <div><h2>Topics</h2><p className="note" style={{ marginTop: 2 }}>Tangled sorts every student question into one of these.</p></div>
            <span className="counter"><Bar value={topics.length / 10} label={`${topics.length} of 10 topics`} />{`${topics.length}/10`}</span>
          </div>
          {loading ? <div style={{ padding: 20 }}><ListSkeleton rows={2} label="Loading topics…" /></div> : topics.length === 0 ?
            <div style={{ padding: 20 }}><Empty icon="overview" title="No topics yet.">Add the first topic below so Tangled can organise course questions.</Empty></div> :
            <div className="topic-list">{topics.map(topic => <article className={`topic-item${editing === topic.id ? " editing" : ""}`} key={topic.id}>
              <div style={{ minWidth: 0 }}><h3 className="truncate" title={topic.name}>{topic.name}</h3><span className="card-meta">{topic.module_label}</span><p>{topic.description}</p></div>
              <div style={{ display: "flex", gap: 6, flex: "none" }}>
                <button className="btn btn-sm" disabled={saving || deleting === topic.id} onClick={() => startEdit(topic)}><Icon name="edit" />Edit</button>
                <button className="btn btn-sm btn-danger" disabled={saving || deleting === topic.id} onClick={() => setPending({ kind: "topic", topic })}>{deleting === topic.id ? "Deleting…" : <><Icon name="trash" />Delete</>}</button>
              </div>
            </article>)}</div>}
        </section>

        <form className="card card-pad form" onSubmit={submit}>
          <div><h2>{editing === null ? "Add a topic" : "Edit topic"}</h2><p className="note" style={{ marginTop: 2 }}>Use the exact names your quiz CSV uses, so scores link up.</p></div>
          <div className="field-row">
            <label className="field">Topic name<input required placeholder="e.g. Gradient descent" value={form.name} onChange={event => updateField("name", event.target.value)} /></label>
            <label className="field">Module label<input required placeholder="e.g. Module 1 · Optimisation" value={form.module_label} onChange={event => updateField("module_label", event.target.value)} /></label>
          </div>
          <label className="field">Description<span className="field-hint">One sentence; Tangled uses it to match questions to this topic.</span><input required placeholder="e.g. Learning rate, gradients and optimisation by gradient descent." value={form.description} onChange={event => updateField("description", event.target.value)} /></label>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <button className="btn btn-primary" disabled={saving || full}>{saving ? "Saving…" : editing === null ? <><Icon name="plus" />Add topic</> : "Save changes"}</button>
            {editing !== null && <button type="button" className="btn btn-ghost" disabled={saving} onClick={cancelEdit}>Cancel</button>}
            {full && <span className="note">You've reached the 10-topic limit.</span>}
          </div>
        </form>
      </div>

      {course && <aside className="setup-side">
        <section className="card card-pad share-card">
          <div><h3>Share with students</h3><p className="note" style={{ marginTop: 2 }}>Students join anonymously with this code. No accounts needed.</p></div>
          <div className="join-code" aria-label={`Join code ${course.join_code}`}>{course.join_code}</div>
          <div className="share-actions"><CopyButton text={joinUrl} label="Copy link" /><CopyButton text={course.join_code} label="Copy code" /></div>
          <p className="note truncate" title={joinUrl}><code>{course.join_link}</code></p>
          <button type="button" className="btn btn-ghost btn-sm" style={{ justifySelf: "start" }} disabled={courseSaving} onClick={() => setPending({ kind: "regenerate" })}><Icon name="refresh" />Regenerate join code</button>
        </section>

        <section className="card card-pad">
          <h3>Course settings</h3>
          <form className="form" style={{ marginTop: 14 }} onSubmit={saveCourse}>
            <label className="field">Course name<input required value={courseName} onChange={event => setCourseName(event.target.value)} /></label>
            <label className="field">Class size<span className="field-hint">Optional. Used to show what share of the class is confused.</span><input type="number" min="1" value={classSize} onChange={event => setClassSize(event.target.value)} /></label>
            <label className="switch">Allow new students to join<input type="checkbox" role="switch" checked={course.joining_open} onChange={event => setCourse(current => current ? { ...current, joining_open: event.target.checked } : current)} /></label>
            <button className="btn btn-primary" disabled={courseSaving}>{courseSaving ? "Saving…" : "Save settings"}</button>
          </form>
        </section>

        <section className="card card-pad danger-zone">
          <h3>Danger zone</h3>
          <p className="note" style={{ margin: "4px 0 12px" }}>Deleting a course removes its topics, materials, questions and insights for good.</p>
          <button type="button" className="btn btn-danger" disabled={courseSaving} onClick={() => setPending({ kind: "course" })}><Icon name="trash" />Delete course</button>
        </section>
      </aside>}
    </div>

    <ConfirmDialog open={pending?.kind === "topic"} danger title="Delete this topic?" confirmLabel="Delete topic"
      body={<p>{pending?.kind === "topic" ? `"${pending.topic.name}" will be removed. Questions linked to it lose their topic, and material tags are rebuilt.` : ""}</p>}
      onConfirm={confirmPending} onCancel={() => setPending(null)} />
    <ConfirmDialog open={pending?.kind === "regenerate"} title="Generate a new join code?" confirmLabel="Regenerate"
      body={<p>Existing join links and the current code will stop working. Students who already joined keep their access.</p>}
      onConfirm={confirmPending} onCancel={() => setPending(null)} />
    <ConfirmDialog open={pending?.kind === "course"} danger title="Delete this course?" confirmLabel="Delete course" requireText={course?.name}
      body={<p>This permanently deletes all of its data, including student questions and insights. It cannot be undone.</p>}
      onConfirm={confirmPending} onCancel={() => setPending(null)} />
    <Toast message={status} onDone={() => setStatus("")} />
  </>;
}
