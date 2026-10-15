import { ChangeEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, friendlyError, QuizRow } from "../api";

export default function Quiz() {
  const { id = "" } = useParams(); const [rows, setRows] = useState<QuizRow[]>([]); const [error, setError] = useState(""); const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false);
  const load = () => api.quiz(id).then(setRows).catch(error => setError(friendlyError(error)));
  useEffect(() => { load(); }, [id]);
  async function importFile(event: ChangeEvent<HTMLInputElement>) { const file = event.target.files?.[0]; if (!file) return; setBusy(true); setError(""); setMessage(""); try { const result = await api.importQuiz(id, file); setMessage(`Imported ${result.imported} aggregate rows.${result.unmatched_concepts.length ? ` Unmatched concepts: ${result.unmatched_concepts.map(item => item.concept).join(", ")}.` : ""}`); load(); } catch (error) { setError(friendlyError(error, "The CSV could not be imported. Check the headers and row numbers.")); } finally { setBusy(false); } }
  if (error && !rows.length) return <div className="state" role="alert"><p>{error}</p><button className="btn" onClick={load}>Try again</button></div>;
  return <><h1>Quiz results</h1><p className="note">Aggregate results only. No student identities are imported or displayed.</p><label className="btn primary">{busy ? "Importing…" : "Import aggregate CSV"}<input hidden type="file" accept=".csv" onChange={importFile} /></label><p aria-live="polite" className={error ? "error" : "success"}>{error || message}</p>{rows.length === 0 ? <div className="empty panel">No quiz results yet.<small>Import an aggregate CSV with item, concept, option, count, correct.</small></div> : <div className="panel"><table><thead><tr><th>Topic</th><th>Answered correctly</th><th>Most common wrong option</th></tr></thead><tbody>{rows.map(row => <tr key={row.item}><td><b>{row.topic}</b><small>{row.item}</small></td><td><div className="bar-label"><b>{Math.round(row.correct_rate * 100)}%</b><span className="bar"><i style={{ width: `${row.correct_rate * 100}%` }} /></span></div></td><td>{row.top_wrong || "—"}</td></tr>)}</tbody></table></div>}</>;
}
