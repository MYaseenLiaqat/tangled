import { useEffect, useState } from "react";
import { api } from "../api";

export default function Materials() {
  const [rows, setRows] = useState<any[]>([]); const [busy, setBusy] = useState(false); const [err, setErr] = useState("");
  const load = () => api.materials().then(setRows);
  useEffect(() => { load(); }, []);
  return (<>
    <h1>Course materials</h1><p className="mute">Upload slides, notes and notebooks. Students read them in the app and ask the AI about them.</p>
    <label className="drop"><b>{busy ? "Indexing…" : "Click to choose files"}</b><span className="mute">PDF, PowerPoint, Word, notebooks, Markdown, text</span>
      <input hidden type="file" multiple accept=".pdf,.pptx,.docx,.ipynb,.md,.txt" onChange={async e => { if (!e.target.files?.length) return; setBusy(true); setErr(""); try { await api.upload(e.target.files); await load(); } catch (x: any) { setErr(String(x.message)); } setBusy(false); }} /></label>
    {err && <p className="bad">{err}</p>}
    <div className="panel"><table><thead><tr><th>File</th><th>Type</th><th>Size</th><th>Sections indexed</th><th>Status</th></tr></thead>
      <tbody>{rows.map(r => <tr key={r.id}><td>{r.filename}</td><td>{r.kind}</td><td>{r.size_kb} KB</td><td>{r.chunks}</td><td><span className="tag ok">{r.status}</span></td></tr>)}</tbody></table></div>
  </>);
}
