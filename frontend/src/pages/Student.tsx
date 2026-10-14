import { FormEvent, useEffect, useState } from "react";
import { api } from "../api";

export default function Student() {
  const [materials, setMaterials] = useState<any[]>([]);
  const [text, setText] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [sessionId] = useState(() => crypto.randomUUID());
  useEffect(() => { api.studentMaterials().then(setMaterials).catch(() => setMaterials([])); }, []);
  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    const question = text; setText("");
    const result = await api.chat(question, sessionId);
    setMessages(old => [...old, { ...result, question }]);
  }
  return <main className="landing"><h1>Course tutor</h1><p className="mute">Your identity is not shown to your instructor; results are combined with other students.</p>
    <section className="panel"><h2>Materials</h2>{materials.map(m => <p key={m.id}>{m.file_url ? <a href={m.file_url} target="_blank" rel="noreferrer">{m.filename}</a> : m.filename} <span className="mute">{m.status}</span></p>)}</section>
    <section className="panel"><h2>Ask a question</h2><form onSubmit={ask}><textarea value={text} maxLength={1000} onChange={e => setText(e.target.value)} /><button className="btn p">Ask</button></form>
      {messages.map(m => <article key={m.message_id}><p><b>You:</b> {m.question}</p><p>{m.answer}</p><button className="btn" onClick={() => api.feedback(m.message_id, "clear")}>Clear</button>{" "}<button className="btn" onClick={() => api.feedback(m.message_id, "unclear")}>Still unclear</button></article>)}</section>
  </main>;
}
