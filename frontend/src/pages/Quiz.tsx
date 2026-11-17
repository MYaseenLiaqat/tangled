import { ChangeEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, friendlyError, QuizRow } from "../api";
import { Icon } from "../ui/Icon";
import { Bar, Empty, ErrorState, ListSkeleton } from "../ui/kit";

/** ok ≥ 75%, warn 60–74%, bad < 60% (the QUIZ_LOW threshold the insights use). */
function tone(rate: number): "ok" | "warn" | "bad" { return rate < .6 ? "bad" : rate < .75 ? "warn" : "ok"; }

export default function Quiz() {
  const { id = "" } = useParams(); const [rows, setRows] = useState<QuizRow[] | null>(null); const [error, setError] = useState(""); const [message, setMessage] = useState(""); const [busy, setBusy] = useState(false);
  const load = () => api.quiz(id).then(setRows).catch(error => { setError(friendlyError(error)); setRows(current => current || []); });
  useEffect(() => { load(); }, [id]);
  async function importFile(event: ChangeEvent<HTMLInputElement>) { const file = event.target.files?.[0]; if (!file) return; setBusy(true); setError(""); setMessage(""); try { const result = await api.importQuiz(id, file); setMessage(`Imported ${result.imported} aggregate rows.${result.unmatched_concepts.length ? ` Unmatched concepts: ${result.unmatched_concepts.map(item => item.concept).join(", ")}.` : ""}`); load(); } catch (error) { setError(friendlyError(error, "The CSV could not be imported. Check the headers and row numbers.")); } finally { setBusy(false); event.target.value = ""; } }
  if (error && rows !== null && rows.length === 0) return <ErrorState message={error} retry={() => { setError(""); setRows(null); load(); }} />;
  const hardest = rows?.length ? [...rows].sort((a, b) => a.correct_rate - b.correct_rate)[0] : null;
  return <>
    <div className="page-head"><div><p className="eyebrow">Assessment signal</p><h1>Quiz results</h1><p className="lead">Aggregate results only. No student identities are imported or displayed.</p></div>
      <label className={`btn btn-primary file-label${busy ? " is-busy" : ""}`} aria-disabled={busy}><Icon name="upload" />{busy ? "Importing…" : "Import aggregate CSV"}<input type="file" accept=".csv" disabled={busy} onChange={importFile} /></label></div>
    <div aria-live="polite">{error ? <p className="alert" role="alert"><Icon name="alert" />{error}</p> : message ? <p className="callout"><Icon name="check" /><span>{message}</span></p> : null}</div>
    {hardest && <div className="callout callout-warn" style={{ marginTop: 16 }}><Icon name="alert" /><span><b>Hardest question</b> · {`${hardest.topic} (${hardest.item}) was answered correctly by ${Math.round(hardest.correct_rate * 100)}% of students.`}</span></div>}
    <section className="section" style={{ marginTop: 20 }}>
      {rows === null ? <ListSkeleton rows={4} label="Loading quiz results…" /> : rows.length === 0 ? <Empty icon="quiz" title="No quiz results yet.">Import an aggregate CSV with the columns item, concept, option, count, correct. Low scores become a second signal for flagging topics.</Empty> :
        <div className="rows" role="table" aria-label="Quiz results">
          <div className="rows-head" role="row"><span role="columnheader">Topic</span><span role="columnheader">Answered correctly</span><span role="columnheader">Top wrong answer</span></div>
          {rows.map(row => { const t = tone(row.correct_rate); return <div className="quiz-row" role="row" key={row.item}>
            <div role="cell" style={{ minWidth: 0 }}><b className="truncate" style={{ display: "block" }} title={row.topic}>{row.topic}</b><span className="card-meta">{`${row.item} · ${row.responses} responses`}</span></div>
            <div role="cell" className={`rate rate-${t}`}><b>{Math.round(row.correct_rate * 100)}%</b><Bar value={row.correct_rate} tone={t} /></div>
            <div role="cell">{row.top_wrong ? <span className="option-chip">{row.top_wrong}</span> : <span className="muted">None</span>}</div>
          </div>; })}
        </div>}
    </section>
  </>;
}
