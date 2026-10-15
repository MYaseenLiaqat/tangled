import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, friendlyError, Material } from "../api";

export default function CourseMaterials() {
  const { id = "" } = useParams();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [error, setError] = useState("");
  const load = () => api.materialsForCourse(id).then(setMaterials).catch(err => setError(friendlyError(err)));
  useEffect(() => { load(); }, [id]);
  useEffect(() => {
    if (!materials.some(material => material.status === "processing")) return;
    const timer = window.setInterval(load, 3000);
    return () => window.clearInterval(timer);
  }, [id, materials]);
  return <main><p><Link to={`/courses/${id}`}>Back to course</Link></p><h1>Materials</h1>
    <p className="mute">Upload course materials for students to search.</p>
    <label className="drop"><b>Click to choose files</b><span className="mute">PDF, PowerPoint, Word, notebooks, Markdown, text</span>
      <input hidden type="file" multiple accept=".pdf,.pptx,.docx,.ipynb,.md,.txt" onChange={async event => {
        if (!event.target.files?.length) return;
        try { await api.uploadMaterials(id, event.target.files); setError(""); load(); } catch (err) { setError(friendlyError(err)); }
      }} />
    </label>
    {error && <p className="bad">{error}</p>}
    <div className="panel"><table><thead><tr><th>File</th><th>Type</th><th>Size</th><th>Chunks</th><th>Status</th><th>Error</th><th /></tr></thead>
      <tbody>{materials.map(material => <tr key={material.id}><td>{material.filename}</td><td>{material.kind}</td><td>{material.size_kb} KB</td><td>{material.chunks}</td><td>{material.status}</td><td className="error">{material.error}</td><td><button className="btn" onClick={async () => { try { await api.deleteMaterial(id, material.id); load(); } catch (error) { setError(friendlyError(error)); } }}>Delete</button></td></tr>)}</tbody>
    </table></div>
  </main>;
}
