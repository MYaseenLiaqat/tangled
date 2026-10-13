import { useEffect, useState } from "react";
import { api } from "../api";

export default function Quiz() {
  const [rows, setRows] = useState<any[]>([]);
  const load = () => api.quiz().then(setRows);
  useEffect(() => { load(); }, []);
  return (<>
    <h1>Quiz results</h1><p className="mute">Each row is one quiz question. The bar shows how many students answered it correctly.</p>
    <label className="btn p">Import results (CSV)<input hidden type="file" accept=".csv" onChange={async e => { if (e.target.files?.[0]) { await api.importQuiz(e.target.files[0]); load(); } }} /></label>
    {rows[0] && <div className="cap"><b>Hardest question:</b> {rows[0].topic}, answered correctly by {Math.round(rows[0].correct_rate * 100)}% of students.</div>}
    <div className="panel"><table><thead><tr><th>Topic</th><th style={{ width: "34%" }}>Answered correctly</th><th>Most common wrong answer</th></tr></thead>
      <tbody>{rows.map(r => <tr key={r.item}><td><b>{r.topic}</b><br /><small className="mute">{r.item}</small></td>
        <td><div className="cnt"><b>{Math.round(r.correct_rate * 100)}%</b><span className="bar"><i style={{ width: r.correct_rate * 100 + "%", background: r.correct_rate < 0.6 ? "var(--rev)" : undefined }} /></span></div></td>
        <td>{r.top_wrong ? <>Option {r.top_wrong.option}<br /><small className="mute">chosen by {r.top_wrong.count} students</small></> : "—"}</td></tr>)}</tbody></table></div>
    <p className="note">A red bar means fewer than 60% of students answered correctly. CSV columns: item, concept, student_code, answer, correct.</p>
  </>);
}
