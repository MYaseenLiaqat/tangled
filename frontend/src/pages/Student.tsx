import { FormEvent, useEffect, useState } from "react";
import { api } from "../api";

export default function Student() {
  const [materials, setMaterials] = useState<any[]>([]);
  const [text, setText] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [feedbackBusy, setFeedbackBusy] = useState<number | null>(null);
  const [feedbackError, setFeedbackError] = useState<number | null>(null);
  const [sessionId] = useState(() => crypto.randomUUID());
  useEffect(() => {
    api.studentMaterials().then(setMaterials).catch(() => setMaterials([]));
    api.studentMessages().then(rows => setMessages(rows)).catch(() => setMessages([]));
  }, []);
  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    const question = text; setText("");
    const result = await api.chat(question, sessionId);
    setMessages(old => [...old, { ...result, question, feedback: "" }]);
  }
  async function setFeedback(messageId: number, value: string) {
    setFeedbackBusy(messageId); setFeedbackError(null);
    try { await api.feedback(messageId, value); setMessages(old => old.map(m => m.message_id === messageId ? { ...m, feedback: value } : m)); }
    catch { setFeedbackError(messageId); }
    finally { setFeedbackBusy(null); }
  }
  return <main className="landing student-page"><div className="page-heading"><div><p className="eyebrow">Student workspace</p><h1>Course tutor</h1><p className="lead">Ask questions grounded in your course materials.</p></div><span className="pill">Anonymous by design</span></div><p className="privacy-note">Your identity is not shown to your instructor; results are combined with other students.</p>
    <section className="panel student-card"><h2>Course materials</h2><p className="note">Open a document to read it while you work through a question.</p><div className="doc-grid">{materials.map(m => <article className="doc-card" key={m.id}>{m.file_url ? <a href={m.file_url} target="_blank" rel="noopener noreferrer">{m.filename}</a> : <b>{m.filename}</b>}<small>{m.status}</small></article>)}</div></section>
    <section className="panel student-card"><h2>Ask a question</h2><p className="note">Tangled answers from the materials and cites the relevant sources.</p><form className="student-form" onSubmit={ask}><textarea aria-label="Your question" value={text} maxLength={1000} onChange={e => setText(e.target.value)} placeholder="What would you like to understand?" /><button className="btn primary">Ask Tangled</button></form>
      {messages.map(m => <article key={m.message_id}><p><b>You:</b> {m.question || ""}</p><p>{m.answer}</p>
        <div aria-live="polite">{m.feedback === "clear" ? "Marked clear ✓" : m.feedback === "unclear" ? "Marked still unclear ✓" : ""}</div>
        <button className="btn" disabled={feedbackBusy === m.message_id} onClick={() => setFeedback(m.message_id, "clear")}>Clear</button>{" "}
        <button className="btn" disabled={feedbackBusy === m.message_id} onClick={() => setFeedback(m.message_id, "unclear")}>Still unclear</button>
        {feedbackError === m.message_id && <p className="error" role="alert">Could not save your choice. Please try again.</p>}
      </article>)}</section>
  </main>;
}
