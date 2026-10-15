import { FormEvent, lazy, Suspense, useEffect, useState } from "react";
import { Link, NavLink, Outlet, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { api, Course, friendlyError } from "./api";
import Join from "./pages/Join";
import Student from "./pages/Student";

const Topics = lazy(() => import("./pages/Topics"));
const TopicDetail = lazy(() => import("./pages/TopicDetail"));
const Quiz = lazy(() => import("./pages/Quiz"));
const Materials = lazy(() => import("./pages/CourseMaterials"));
const TopicsSetup = lazy(() => import("./pages/TopicsSetup"));

function Auth() {
  const navigate = useNavigate();
  const [registering, setRegistering] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const result = await (registering ? api.register(email, password) : api.login(email, password));
      localStorage.setItem("instructor_token", result.access_token); navigate("/courses");
    } catch (error) { setError(friendlyError(error, "We could not sign you in. Check your details and try again.")); }
    finally { setBusy(false); }
  }
  return <main className="auth-page">
    <div className="auth-brand"><span className="brand-mark">t</span><span>Tangled</span></div>
    <section className="auth-card"><p className="eyebrow">Instructor workspace</p>
      <h1>{registering ? "Create your workspace" : "Welcome back"}</h1>
      <p className="lead">{registering ? "Start turning student questions into clear teaching signals." : "See what your class understands, and where they need you next."}</p>
      <form className="form" onSubmit={submit}>
        <label>Email<input required type="email" placeholder="you@university.edu" value={email} onChange={event => setEmail(event.target.value)} /></label>
        <label>Password<input required minLength={8} type="password" placeholder="At least 8 characters" value={password} onChange={event => setPassword(event.target.value)} /></label>
        <button className="btn primary btn-block" disabled={busy}>{busy ? "Working…" : registering ? "Create account" : "Log in"}</button>
        {error && <p className="error" role="alert">{error}</p>}
      </form>
      <button type="button" className="text-button" onClick={() => setRegistering(!registering)}>{registering ? "Already have an account? Log in" : "New to Tangled? Create an account"}</button>
    </section>
  </main>;
}

function Courses() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [name, setName] = useState(""); const [classSize, setClassSize] = useState("");
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const load = () => api.courses().then(setCourses).catch(error => setError(friendlyError(error)));
  useEffect(() => { load(); }, []);
  async function create(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { await api.createCourse(name, classSize ? Number(classSize) : undefined); setName(""); setClassSize(""); load(); }
    catch (error) { setError(friendlyError(error)); } finally { setBusy(false); }
  }
  return <main className="landing courses-page">
    <div className="page-heading"><div><p className="eyebrow">Instructor workspace</p><h1>Your courses</h1><p className="lead">Choose a course to review its learning signals.</p></div><span className="avatar">I</span></div>
    <section className="panel create-course"><div><h2>Create a course</h2><p className="note">Set up a space for your students and their questions.</p></div>
      <form className="inline-form" onSubmit={create}><input required placeholder="Course name" value={name} onChange={event => setName(event.target.value)} /><input type="number" min="1" placeholder="Class size (optional)" value={classSize} onChange={event => setClassSize(event.target.value)} /><button className="btn primary" disabled={busy}>{busy ? "Creating…" : "Create course"}</button></form>
      {error && <p className="error" role="alert">{error}</p>}
    </section>
    <div className="course-grid">{courses.map(course => <Link className="course-card" key={course.id} to={`/courses/${course.id}/topics`}><div className="course-icon">∿</div><div><h2>{course.name}</h2><p className="note">Join code <strong>{course.join_code}</strong></p></div><span className="arrow">→</span></Link>)}</div>
    {courses.length === 0 && <div className="empty panel">No courses yet.<small>Create your first course above to get started.</small></div>}
  </main>;
}

function Layout() {
  const { id = "" } = useParams(); const [course, setCourse] = useState<Course | null>(null); const [error, setError] = useState("");
  useEffect(() => { api.course(id).then(setCourse).catch(error => setError(friendlyError(error))); }, [id]);
  if (error) return <main className="state" role="alert"><p>{error}</p><Link className="btn" to="/courses">Back to courses</Link></main>;
  if (!course) return <main className="state"><p>Loading course…</p></main>;
  return <div className="shell"><aside className="side">
    <Link className="logo" to="/courses"><span className="brand-mark">t</span><span>Tangled</span></Link><p className="side-label">Course workspace</p>
    <NavLink to={`/courses/${id}/topics`}><span>◈</span> Overview</NavLink><NavLink to={`/courses/${id}/quiz`}><span>▤</span> Quiz results</NavLink><NavLink to={`/courses/${id}/materials`}><span>□</span> Materials</NavLink><NavLink to={`/courses/${id}/setup`}><span>⚙</span> Topic setup</NavLink>
    <div className="side-spacer" /><Link to="/courses"><span>←</span> All courses</Link>
  </aside><div className="wrap"><header className="top"><div><span className="breadcrumb">Course workspace / </span><strong>{course.name}</strong></div><div className="top-actions"><span className="top-note">Instructor view</span><span className="avatar">I</span></div></header>
    <main><Suspense fallback={<div className="state"><p>Loading page…</p></div>}><Outlet /></Suspense></main>
  </div></div>;
}

export default function App() {
  return <Routes><Route path="/" element={<Auth />} /><Route path="/courses" element={<Courses />} /><Route path="/join/:code" element={<Join />} /><Route path="/student" element={<Student />} /><Route path="/courses/:id" element={<Layout />}><Route index element={<Topics />} /><Route path="topics" element={<Topics />} /><Route path="topics/:topicId" element={<TopicDetail />} /><Route path="quiz" element={<Quiz />} /><Route path="materials" element={<Materials />} /><Route path="setup" element={<TopicsSetup />} /></Route></Routes>;
}
