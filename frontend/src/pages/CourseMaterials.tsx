import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, friendlyError, Material } from "../api";

export default function CourseMaterials() {
  const { id = "" } = useParams();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const load = () => api.materialsForCourse(id).then(setMaterials).catch(err => setError(friendlyError(err)));
  useEffect(() => { load(); }, [id]);
  useEffect(() => {
    if (!materials.some(material => material.status === "processing")) return;
    const timer = window.setInterval(load, 3000);
    return () => window.clearInterval(timer);
  }, [id, materials]);
  return <main><p><Link className="back" to={`/courses/${id}`}>← Back to overview</Link></p><div className="page-heading"><div><p className="eyebrow">Course library</p><h1>Materials</h1><p className="note">Upload course materials for students to search.</p></div><span className="pill">50 files max</span></div>
    <label className="drop"><span className="upload-icon">↑</span><b>{busy ? "Indexing files…" : "Upload course materials"}</b><span className="mute">Drop files here or click to browse · PDF, PowerPoint, Word, notebooks, Markdown, text</span>
      <input hidden type="file" multiple accept=".pdf,.pptx,.docx,.ipynb,.md,.txt" onChange={async event => {
        if (!event.target.files?.length) return;
        setBusy(true);
        try { await api.uploadMaterials(id, event.target.files); setError(""); load(); } catch (err) { setError(friendlyError(err)); } finally { setBusy(false); }
      }} />
    </label>
    {error && <p className="error" role="alert">{error}</p>}
    {materials.length === 0 ? <div className="empty panel">No materials uploaded yet.<small>Add your course outline, slides or notes so students can ask grounded questions.</small></div> :
      <div className="panel table-wrap"><table><thead><tr><th>File</th><th>Type</th><th>Size</th><th>Sections</th><th>Status</th><th /></tr></thead>
        <tbody>{materials.map(material => <tr key={material.id}><td><b>{material.filename}</b>{material.error && <small className="error">{material.error}</small>}</td><td><span className="pill">{material.kind}</span></td><td>{material.size_kb} KB</td><td>{material.chunks || "—"}</td><td><span className={`tag ${material.status === "indexed" ? "addressed" : material.status === "failed" ? "review" : "monitor"}`}>{material.status}</span></td><td><button className="btn btn-small" onClick={async () => { try { await api.deleteMaterial(id, material.id); load(); } catch (error) { setError(friendlyError(error)); } }}>Delete</button></td></tr>)}</tbody>
      </table></div>}
  </main>;
}
