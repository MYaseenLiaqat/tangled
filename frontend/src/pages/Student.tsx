import { useEffect, useRef, useState } from "react";
import { api, studentCode } from "../api";

type Msg = { me: boolean; text: string; id?: number; sources?: any[] };
export default function Student() {
  const [mats, setMats] = useState<any[]>([]); const [sel, setSel] = useState<any>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]); const [text, setText] = useState(""); const [busy, setBusy] = useState(false);
  const sid = useRef(crypto.randomUUID()); const end = useRef<HTMLDivElement>(null);
  useEffect(() => { api.sMaterials().then(setMats); }, []);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);
  async function ask() {
    const q = text.trim(); if (!q || busy) return; setText(""); setBusy(true); setMsgs(m => [...m, { me: true, text: q }]);
    try { const r = await api.chat(q, sid.current); setMsgs(m => [...m, { me: false, text: r.answer, id: r.message_id, sources: r.sources }]); }
    catch { setMsgs(m => [...m, { me: false, text: "Something went wrong. Please try again." }]); }
    setBusy(false);
  }
  return (<div className="stu">
    <div className="host"><b>Your learning platform</b> › AI/ML – Deep Learning › Materials</div>
    <div className="read">
      <div><h2>Course materials</h2>
        <div className="lib">{mats.map(m => <button key={m.id} className={"doc" + (sel?.id === m.id ? " on" : "")} onClick={() => setSel(m)}><span className="pill">{m.kind}</span><b>{m.filename}</b></button>)}</div>
        {sel && (sel.filename.toLowerCase().endsWith(".pdf")
          ? <iframe title={sel.filename} className="frame" src={`/api/student/materials/${sel.id}/file?code=${studentCode()}`} />
          : <p className="mute">Preview for this file type is not built yet. <a href={`/api/student/materials/${sel.id}/file?code=${studentCode()}`}>Download</a></p>)}</div>
      <div className="chat"><b>Ask the AI about this material</b>
        <div className="msgs">{msgs.length === 0 && <div className="bub">Hi! Ask me anything about your course. I answer from your materials.</div>}
          {msgs.map((m, i) => <div key={i} className={"bub" + (m.me ? " me" : "")}>{m.text}
            {m.sources?.length ? <small>Sources: {m.sources.map(s => `[${s.n}] ${s.material}, ${s.section}`).join(" · ")}</small> : null}
            {m.id && <span className="fb"><button onClick={() => api.feedback(m.id!, "clear")}>Clear</button><button onClick={() => api.feedback(m.id!, "unclear")}>Still unclear</button></span>}</div>)}<div ref={end} /></div>
        <div className="inp"><input value={text} placeholder="Type your question" onChange={e => setText(e.target.value)} onKeyDown={e => e.key === "Enter" && ask()} /><button className="btn p" disabled={busy} onClick={ask}>Ask</button></div></div>
    </div></div>);
}
