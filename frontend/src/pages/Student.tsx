import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { api, StudentSource } from "../api";
import { friendlyError } from "../utils/errors";
import { renderAnswer } from "../utils/answer";
import { Brand } from "../ui/Brand";
import { Icon, kindIcon } from "../ui/Icon";
import { Empty, Skeleton } from "../ui/kit";

function validSources(sources: StudentSource[] | undefined): StudentSource[] {
  return (sources || []).filter(source => Number.isInteger(source.n) && source.n > 0 &&
    Boolean(source.material || source.section));
}

export default function Student() {
  const [materials, setMaterials] = useState<any[]>([]);
  const [text, setText] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState("");
  const [error, setError] = useState("");
  const [feedbackBusy, setFeedbackBusy] = useState<number | null>(null);
  const [feedbackError, setFeedbackError] = useState<number | null>(null);
  const [sessionId] = useState(() => crypto.randomUUID());
  const bottom = useRef<HTMLDivElement>(null);
  useEffect(() => {
    Promise.all([api.studentMaterials(), api.studentMessages()])
      .then(([loadedMaterials, loadedMessages]) => { setMaterials(loadedMaterials); setMessages(loadedMessages); setError(""); })
      .catch(err => setError(friendlyError(err, "We could not load your course. Please sign in again.")))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => { bottom.current?.scrollIntoView?.({ behavior: "smooth", block: "end" }); }, [messages.length, busy]);
  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    const question = text.trim(); setText(""); setBusy(true); setError(""); setPendingQuestion(question);
    try {
      const result = await api.chat(question, sessionId);
      setMessages(old => [...old, { ...result, question, feedback: "" }]);
    } catch (err) {
      setText(question);
      setError(friendlyError(err, "The tutor is temporarily unavailable. Please try again."));
    } finally { setBusy(false); setPendingQuestion(""); }
  }
  async function setFeedback(messageId: number, value: string) {
    setFeedbackBusy(messageId); setFeedbackError(null);
    try { await api.feedback(messageId, value); setMessages(old => old.map(m => m.message_id === messageId ? { ...m, feedback: value } : m)); }
    catch { setFeedbackError(messageId); }
    finally { setFeedbackBusy(null); }
  }
  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); }
  }
  const courseName = localStorage.getItem("student_course_name") || "Your course";

  if (loading) return <><header className="student-top"><Brand /></header><main className="student-main" role="status" aria-label="Loading your course…">
    <Skeleton w={120} h={12} /><Skeleton w="60%" h={30} style={{ marginTop: 10 }} /><div className="doc-chips"><Skeleton w={160} h={34} /><Skeleton w={140} h={34} /><Skeleton w={180} h={34} /></div>
    <div className="thread"><Skeleton w="50%" h={42} style={{ justifySelf: "end", borderRadius: 16 }} /><Skeleton h={140} r={14} /></div></main></>;

  return <>
    <header className="student-top"><Brand /><span className="pill pill-brand"><Icon name="lock" />Anonymous by design</span></header>
    <main className="student-main">
      <p className="eyebrow">Course tutor</p>
      <h1 className="clamp-2" title={courseName}>{courseName}</h1>
      <p className="lead">Ask questions grounded in your course materials. Your identity is not shown to your instructor; results are combined with other students.</p>
      <div className="doc-chips" aria-label="Course materials">{materials.length === 0 ? <span className="note">Your instructor has not indexed any materials yet.</span> :
        materials.map(m => m.file_url
          ? <a className="doc-chip" key={m.id} href={m.file_url} target="_blank" rel="noopener noreferrer" title={`Open ${m.filename}`}><Icon name={kindIcon(m.filename)} /><span className="truncate">{m.filename}</span></a>
          : <span className="doc-chip" key={m.id} title={`${m.filename} (${m.status})`}><Icon name={kindIcon(m.filename)} /><span className="truncate">{m.filename}</span></span>)}</div>

      <div className="thread" aria-live="polite">
        {messages.length === 0 && !busy && <Empty icon="message" title="Ready when you are.">Ask about anything in your course materials. Tangled answers from them and shows its sources.</Empty>}
        {messages.map(m => {
          const sources = validSources(m.sources);
          return <article className="turn" key={m.message_id}>
            <p className="q-bubble"><span className="sr-only">You: </span>{m.question || ""}</p>
            <div className="card a-card">
              <div className="a-head"><span className="brand-mark" aria-hidden="true">t</span>Tangled</div>
              {renderAnswer(m.answer || "", sources.map(source => source.n))}
              {sources.length > 0 && <div className="sources"><b>Sources</b><ul>{sources.map(source =>
                <li key={`${m.message_id}-${source.n}`}><span className="cite-num">{source.n}</span><span>{source.material || "Course material"}{source.section ? ` — ${source.section}` : ""}</span></li>
              )}</ul></div>}
              <div className="feedback">
                <span className="feedback-label">Did this help?</span>
                <button className="toggle toggle-ok" aria-pressed={m.feedback === "clear"} disabled={feedbackBusy === m.message_id} onClick={() => setFeedback(m.message_id, "clear")}><Icon name="check" />Clear</button>
                <button className="toggle toggle-warn" aria-pressed={m.feedback === "unclear"} disabled={feedbackBusy === m.message_id} onClick={() => setFeedback(m.message_id, "unclear")}><Icon name="info" />Still unclear</button>
                <span className="sr-only" aria-live="polite">{m.feedback === "clear" ? "Marked clear ✓" : m.feedback === "unclear" ? "Marked still unclear ✓" : ""}</span>
              </div>
              {feedbackError === m.message_id && <p className="error small" role="alert">Could not save your choice. Please try again.</p>}
            </div>
          </article>;
        })}
        {busy && <div className="turn"><p className="q-bubble">{pendingQuestion}</p><div className="card a-card"><div className="a-head"><span className="brand-mark" aria-hidden="true">t</span>Tangled is reading your materials <span className="typing" aria-label="Thinking"><i /><i /><i /></span></div><Skeleton h={12} w="92%" /><Skeleton h={12} w="78%" /><Skeleton h={12} w="54%" /></div></div>}
        <div ref={bottom} />
      </div>

      <div className="composer-wrap">
        {error && <p className="alert" role="alert" style={{ marginBottom: 10 }}><Icon name="alert" />{error}</p>}
        <form className="composer" onSubmit={ask}>
          <textarea aria-label="Your question" value={text} maxLength={1000} rows={1} onKeyDown={onKeyDown} onChange={e => setText(e.target.value)} placeholder="What would you like to understand?" disabled={busy} />
          <button className="btn btn-primary" disabled={busy || !text.trim()} aria-label={busy ? "Thinking…" : "Ask Tangled"}>{busy ? "Thinking…" : <>Ask<Icon name="send" /></>}</button>
        </form>
        <p className="composer-hint">Enter to send · Shift + Enter for a new line</p>
      </div>
    </main>
  </>;
}
