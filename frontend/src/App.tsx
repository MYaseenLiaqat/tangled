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
  const navigate = useNavigate(); const [registering, setRegistering] = useState(false); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(""); try { const result = await (registering ? api.register(email, password) : api.login(email, password)); localStorage.setItem("instructor_token", result.access_token); navigate("/courses"); } catch (error) { setError(friendlyError(error, "We could not sign you in. Check your details and try again.")); } finally { setBusy(false); } }
  return <main className="landing"><h1>Tangled</h1><form className="panel form" onSubmit={submit}><h2>{registering ? "Create instructor account" : "Instructor login"}</h2><input required type="email" placeholder="Email" value={email} onChange={event => setEmail(event.target.value)} /><input required minLength={8} type="password" placeholder="Password" value={password} onChange={event => setPassword(event.target.value)} /><button className="btn primary" disabled={busy}>{busy ? "Working…" : registering ? "Register" : "Log in"}</button>{error && <p className="error" role="alert">{error}</p>}<button type="button" className="btn" onClick={() => setRegistering(!registering)}>{registering ? "Already registered?" : "Create an account"}</button></form></main>;
}

function Courses() {
  const [courses, setCourses] = useState<Course[]>([]); const [name, setName] = useState(""); const [classSize, setClassSize] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const load = () => api.courses().then(setCourses).catch(error => setError(friendlyError(error)));
  useEffect(() => { load(); }, []);
  async function create(event: FormEvent) { event.preventDefault(); setBusy(true); try { await api.createCourse(name, classSize ? Number(classSize) : undefined); setName(""); setClassSize(""); load(); } catch (error) { setError(friendlyError(error)); } finally { setBusy(false); } }
  return <main className="landing"><h1>Your courses</h1><form className="panel form" onSubmit={create}><input required placeholder="Course name" value={name} onChange={event => setName(event.target.value)} /><input type="number" min="1" placeholder="Class size (optional)" value={classSize} onChange={event => setClassSize(event.target.value)} /><button className="btn primary" disabled={busy}>{busy ? "Creating…" : "Create course"}</button>{error && <p className="error" role="alert">{error}</p>}</form><div className="card-grid">{courses.map(course => <Link className="topic-card" key={course.id} to={`/courses/${course.id}/topics`}><h2>{course.name}</h2><p className="note">Join code: {course.join_code}</p></Link>)}</div></main>;
}

function Layout() {
  const { id = "" } = useParams(); const [course, setCourse] = useState<Course | null>(null); const [error, setError] = useState("");
  useEffect(() => { api.course(id).then(setCourse).catch(error => setError(friendlyError(error))); }, [id]);
  if (error) return <main className="state" role="alert"><p>{error}</p><Link className="btn" to="/courses">Back to courses</Link></main>;
  if (!course) return <main className="state"><p>Loading course…</p></main>;
  return <div className="shell"><aside className="side"><Link className="logo" to="/courses">Tangled</Link><NavLink to={`/courses/${id}/topics`}>Topics</NavLink><NavLink to={`/courses/${id}/quiz`}>Quiz results</NavLink><NavLink to={`/courses/${id}/materials`}>Materials</NavLink><NavLink to={`/courses/${id}/setup`}>Topic setup</NavLink><Link to="/courses">All courses</Link></aside><div className="wrap"><header className="top"><h1>{course.name}</h1><span className="note">Instructor view</span></header><main><Suspense fallback={<div className="state"><p>Loading page…</p></div>}><Outlet /></Suspense></main></div></div>;
}

export default function App() {
  return <Routes><Route path="/" element={<Auth />} /><Route path="/courses" element={<Courses />} /><Route path="/join/:code" element={<Join />} /><Route path="/student" element={<Student />} /><Route path="/courses/:id" element={<Layout />}><Route index element={<Topics />} /><Route path="topics" element={<Topics />} /><Route path="topics/:topicId" element={<TopicDetail />} /><Route path="quiz" element={<Quiz />} /><Route path="materials" element={<Materials />} /><Route path="setup" element={<TopicsSetup />} /></Route></Routes>;
}
