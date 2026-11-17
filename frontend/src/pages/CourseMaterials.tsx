import { DragEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, friendlyError, Material } from "../api";
import { Icon, kindIcon } from "../ui/Icon";
import { ConfirmDialog, Empty, ListSkeleton } from "../ui/kit";

function size(kb: number) { return kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`; }

export default function CourseMaterials() {
  const { id = "" } = useParams();
  const [materials, setMaterials] = useState<Material[] | null>(null);
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [confirm, setConfirm] = useState<Material | null>(null);
  const load = () => api.materialsForCourse(id).then(setMaterials).catch(err => { setError(friendlyError(err)); setMaterials(current => current || []); });
  useEffect(() => { load(); }, [id]);
  useEffect(() => {
    if (!materials?.some(material => material.status === "processing")) return;
    const timer = window.setInterval(load, 3000);
    return () => window.clearInterval(timer);
  }, [id, materials]);
  async function upload(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    try { await api.uploadMaterials(id, files); setError(""); await load(); } catch (err) { setError(friendlyError(err)); } finally { setBusy(false); }
  }
  async function remove(material: Material) {
    setConfirm(null);
    try { await api.deleteMaterial(id, material.id); load(); } catch (error) { setError(friendlyError(error)); }
  }
  function drop(event: DragEvent<HTMLLabelElement>) { event.preventDefault(); setDragging(false); upload(event.dataTransfer.files); }
  const indexed = materials?.filter(m => m.status === "indexed").length || 0;
  return <>
    <div className="page-head"><div><p className="eyebrow">Course library</p><h1>Materials</h1><p className="lead">Upload course materials for students to search. Tangled answers only from these.</p></div><span className="pill tnum">{`${materials?.length || 0} / 50 files`}</span></div>
    <label className={`dropzone${dragging ? " dragging" : ""}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={drop}>
      <span className="empty-icon"><Icon name="upload" /></span>
      <b>{busy ? "Uploading…" : "Upload course materials"}</b>
      <span className="note">Drop files here or click to browse · PDF, PowerPoint, Word, notebooks, Markdown, text · up to 25 MB each</span>
      <input type="file" multiple accept=".pdf,.pptx,.docx,.ipynb,.md,.txt" disabled={busy} onChange={event => { upload(event.target.files); event.target.value = ""; }} />
    </label>
    {error && <p className="alert" role="alert" style={{ marginTop: 14 }}><Icon name="alert" />{error}</p>}
    <section className="section" style={{ marginTop: 24 }}>
      <div className="section-head"><div><h2>Library</h2>{materials && materials.length > 0 && <p className="note tnum">{`${indexed} of ${materials.length} ready for students`}</p>}</div></div>
      {materials === null ? <ListSkeleton rows={3} label="Loading materials…" /> : materials.length === 0 ? <Empty icon="files" title="No materials uploaded yet.">Add your course outline, slides or notes so students can ask grounded questions.</Empty> :
        <div className="card">{materials.map(material => <div className="file-row" key={material.id}>
          <span className="file-icon"><Icon name={kindIcon(material.kind)} /></span>
          <div style={{ minWidth: 0 }}><div className="file-name truncate" title={material.filename}>{material.filename}</div>
            <div className="file-meta">{`${material.kind} · ${size(material.size_kb)}${material.chunks ? ` · ${material.chunks} sections` : ""}`}</div>
            {material.error && <div className="file-error">{material.error}</div>}</div>
          <span className={`status status-${material.status}`}><span className="dot" />{material.status}</span>
          <span className="row-actions"><button className="btn btn-ghost btn-sm icon-btn" aria-label={`Delete ${material.filename}`} title="Delete" onClick={() => setConfirm(material)}><Icon name="trash" /></button></span>
        </div>)}</div>}
    </section>
    <ConfirmDialog open={confirm !== null} title="Delete this file?" danger confirmLabel="Delete file"
      body={<p>{`"${confirm?.filename}" will be removed from the library, and students will no longer get answers from it.`}</p>}
      onConfirm={() => confirm && remove(confirm)} onCancel={() => setConfirm(null)} />
  </>;
}
