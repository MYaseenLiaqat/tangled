import { FormEvent, lazy, Suspense, useEffect, useState } from "react";
import { Link, NavLink, Navigate, Outlet, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { api, Course, friendlyError } from "./api";
import Join from "./pages/Join";
import Student from "./pages/Student";
import Consent from "./pages/Consent";
import { Icon } from "./ui/Icon";
import { CopyButton, Empty, ListSkeleton } from "./ui/kit";
import { Brand } from "./ui/Brand";

const Topics = lazy(() => import("./pages/Topics"));
const TopicDetail = lazy(() => import("./pages/TopicDetail"));
const Quiz = lazy(() => import("./pages/Quiz"));
const Materials = lazy(() => import("./pages/CourseMaterials"));
const TopicsSetup = lazy(() => import("./pages/TopicsSetup"));

function RequireToken({ kind, children }: { kind: "instructor" | "student"; children: JSX.Element }) {
  const key = kind === "instructor" ? "instructor_token" : "student_token";
  return localStorage.getItem(key) ? children : <Navigate to="/" replace />;
}

function logOut() { localStorage.removeItem("instructor_token"); window.location.assign("/"); }

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

  return <main className="auth">
    <div className="auth-top"><Brand /></div>
    <section className="auth-card"><p className="eyebrow">Instructor workspace</p>
      <h1>{registering ? "Create your workspace" : "Welcome back"}</h1>
      <p className="lead">{registering ? "Start turning student questions into clear teaching signals." : "See what your class understands, and where they need you next."}</p>
      <form className="form" onSubmit={submit}>
        <label className="field">Email<input required type="email" autoComplete="email" placeholder="you@university.edu" value={email} onChange={event => setEmail(event.target.value)} /></label>
        <label className="field">Password<input required minLength={8} type="password" autoComplete={registering ? "new-password" : "current-password"} placeholder="At least 8 characters" value={password} onChange={event => setPassword(event.target.value)} /></label>
        {error && <p className="alert" role="alert"><Icon name="alert" />{error}</p>}
        <button className="btn btn-primary btn-lg btn-block" disabled={busy}>{busy ? "Working…" : registering ? "Create account" : "Log in"}</button>
      </form>
      <div className="auth-foot">
        <button type="button" className="text-button" style={{ justifySelf: "start" }} onClick={() => setRegistering(!registering)}>{registering ? "Already have an account? Log in" : "New to Tangled? Create an account"}</button>
        <p className="student-entry">Are you a student? <Link to="/join">Join your course with a code →</Link></p>
      </div>
    </section>
  </main>;
}

function Courses() {
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [name, setName] = useState(""); const [classSize, setClassSize] = useState("");
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const load = () => api.courses().then(setCourses).catch(error => { setError(friendlyError(error)); setCourses([]); });
  useEffect(() => { load(); }, []);
  async function create(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { await api.createCourse(name, classSize ? Number(classSize) : undefined); setName(""); setClassSize(""); load(); }
    catch (error) { setError(friendlyError(error)); } finally { setBusy(false); }
  }
  return <div className="page-narrow">
    <header className="topbar"><Brand /><div className="coursebar-actions"><button className="btn btn-ghost btn-sm" onClick={logOut}><Icon name="logout" />Log out</button><span className="avatar" aria-hidden="true">I</span></div></header>
    <div className="page-head"><div><p className="eyebrow">Instructor workspace</p><h1>Your courses</h1><p className="lead">Choose a course to review its learning signals.</p></div></div>
    <section className="card card-pad create-card"><div><h2>Create a course</h2><p className="note" style={{ marginTop: 4 }}>Set up a space for your students and their questions.</p></div>
      <form className="inline-form" onSubmit={create}>
        <label className="sr-only" htmlFor="course-name">Course name</label><input id="course-name" required placeholder="Course name" value={name} onChange={event => setName(event.target.value)} />
        <label className="sr-only" htmlFor="class-size">Class size</label><input id="class-size" type="number" min="1" placeholder="Class size (optional)" value={classSize} onChange={event => setClassSize(event.target.value)} />
        <button className="btn btn-primary" style={{ height: 40 }} disabled={busy}><Icon name="plus" />{busy ? "Creating…" : "Create course"}</button>
      </form>
      {error && <p className="alert" role="alert" style={{ gridColumn: "1 / -1" }}><Icon name="alert" />{error}</p>}
    </section>
    <section className="section">
      <div className="section-head"><h2>Courses</h2></div>
      {courses === null ? <ListSkeleton rows={2} height={80} label="Loading courses…" /> : courses.length === 0 ?
        <Empty icon="course" title="No courses yet.">Create your first course above to get started. You'll get a join code to share with your students.</Empty> :
        <div className="course-grid">{courses.map(course => <Link className="card card-link course-card" key={course.id} to={`/courses/${course.id}/topics`} title={course.name}>
          <span className="course-icon"><Icon name="course" /></span>
          <span style={{ minWidth: 0 }}><span className="card-title clamp-2">{course.name}</span><span className="card-meta">Join code <b className="tnum" style={{ color: "var(--ink)", fontFamily: "var(--mono)", letterSpacing: ".08em" }}>{course.join_code}</b></span></span>
          <span className="arrow"><Icon name="arrow" /></span>
        </Link>)}</div>}
    </section>
  </div>;
}

function Layout() {
  const { id = "" } = useParams(); const [course, setCourse] = useState<Course | null>(null); const [error, setError] = useState("");
  useEffect(() => { api.course(id).then(setCourse).catch(error => setError(friendlyError(error))); }, [id]);
  if (error) return <main className="state" role="alert"><p>{error}</p><Link className="btn" to="/courses"><Icon name="back" />Back to courses</Link></main>;
  if (!course) return <main className="state" role="status"><p>Loading course…</p></main>;
  const joinUrl = `${window.location.origin}/join/${course.join_code}`;
  return <div className="shell"><aside className="sidebar">
    <Brand to="/courses" />
    <p className="nav-label">Course</p>
    <nav className="nav" aria-label="Course">
      <NavLink to={`/courses/${id}/topics`}><Icon name="overview" />Overview</NavLink>
      <NavLink to={`/courses/${id}/quiz`}><Icon name="quiz" />Quiz results</NavLink>
      <NavLink to={`/courses/${id}/materials`}><Icon name="files" />Materials</NavLink>
      <NavLink to={`/courses/${id}/setup`}><Icon name="settings" />Topic setup</NavLink>
    </nav>
    <div className="sidebar-spacer" />
    <nav className="nav nav-secondary" aria-label="Account">
      <Link to="/courses"><Icon name="back" />All courses</Link>
      <button type="button" onClick={logOut}><Icon name="logout" />Log out</button>
    </nav>
  </aside><div className="main-col"><header className="coursebar">
      <div className="coursebar-title"><span className="crumb">Courses /</span><strong className="truncate" title={course.name}>{course.name}</strong></div>
      <div className="coursebar-actions"><span className="code-chip" title="Students join with this code">Join code <b>{course.join_code}</b><CopyButton text={joinUrl} label="Copy link" className="btn btn-ghost btn-sm" /></span><span className="avatar" aria-hidden="true">I</span></div>
    </header>
    <main className="content"><Suspense fallback={<ListSkeleton rows={3} height={90} label="Loading page…" />}><Outlet /></Suspense></main>
  </div></div>;
}

export default function App() {
  return <Routes><Route path="/" element={<Auth />} /><Route path="/courses" element={<RequireToken kind="instructor"><Courses /></RequireToken>} /><Route path="/join/:code?" element={<Join />} /><Route path="/consent/:code?" element={<Consent />} /><Route path="/student" element={<RequireToken kind="student"><Student /></RequireToken>} /><Route path="/courses/:id" element={<RequireToken kind="instructor"><Layout /></RequireToken>}><Route index element={<Topics />} /><Route path="topics" element={<Topics />} /><Route path="topics/:topicId" element={<TopicDetail />} /><Route path="quiz" element={<Quiz />} /><Route path="materials" element={<Materials />} /><Route path="setup" element={<TopicsSetup />} /></Route></Routes>;
}
