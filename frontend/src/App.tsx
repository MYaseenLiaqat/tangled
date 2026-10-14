import { FormEvent, useEffect, useState } from "react";
import { Link, Outlet, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { api } from "./api";
import TopicsSetup from "./pages/TopicsSetup";
import CourseMaterials from "./pages/CourseMaterials";

function Auth() {
  const navigate = useNavigate();
  const [registering, setRegistering] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const result = await (registering ? api.register(email, password) : api.login(email, password));
      localStorage.setItem("instructor_token", result.access_token);
      navigate("/courses");
    } catch (err) { setError(String(err)); }
  }
  return <main className="landing"><h1>Tangled</h1><form className="panel" onSubmit={submit}>
    <h2>{registering ? "Create instructor account" : "Instructor login"}</h2>
    <input required type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
    <input required minLength={8} type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
    <button className="btn p" type="submit">{registering ? "Register" : "Log in"}</button>
    {error && <p className="bad">{error}</p>}
    <button type="button" className="btn" onClick={() => setRegistering(!registering)}>{registering ? "Already registered?" : "Create an account"}</button>
  </form></main>;
}

function Courses() {
  const [courses, setCourses] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [classSize, setClassSize] = useState("");
  const load = () => api.courses().then(setCourses);
  useEffect(() => { load(); }, []);
  async function create(event: FormEvent) {
    event.preventDefault();
    await api.createCourse(name, classSize ? Number(classSize) : undefined);
    setName(""); setClassSize(""); load();
  }
  return <main className="landing"><h1>Your courses</h1><form className="panel" onSubmit={create}>
    <input required placeholder="Course name" value={name} onChange={e => setName(e.target.value)} />
    <input type="number" min="1" placeholder="Class size (optional)" value={classSize} onChange={e => setClassSize(e.target.value)} />
    <button className="btn p">Create course</button>
  </form><div className="grid2">{courses.map(course => <Link className="card" key={course.id} to={`/courses/${course.id}`}><h2>{course.name}</h2><p className="mute">Join code: {course.join_code}</p></Link>)}</div></main>;
}

function Course() {
  const { id = "" } = useParams();
  const [course, setCourse] = useState<any>();
  useEffect(() => { api.course(id).then(setCourse); }, [id]);
  if (!course) return <main className="landing"><p>Loading...</p></main>;
  async function toggle() { setCourse(await api.updateCourse(id, { joining_open: !course.joining_open })); }
  async function regenerate() { setCourse(await api.regenerateCode(id)); }
  const link = `${window.location.origin}${course.join_link}`;
  return <main className="landing"><p><Link to="/courses">All courses</Link></p><h1>{course.name}</h1>
    <div className="panel"><h2>Student join</h2><p>Code: <b>{course.join_code}</b></p><p>{link}</p>
      <button className="btn" onClick={() => navigator.clipboard.writeText(link)}>Copy link</button>
      <button className="btn" onClick={() => navigator.clipboard.writeText(course.join_code)}>Copy code</button>
      <button className="btn" onClick={regenerate}>Regenerate code</button>
      <button className="btn p" onClick={toggle}>{course.joining_open ? "Close joining" : "Open joining"}</button>
      <p className="mute">Joining is {course.joining_open ? "open" : "closed"}.</p>
      <p><Link className="btn" to={`/courses/${id}/topics`}>Topics</Link>{" "}
        <Link className="btn" to={`/courses/${id}/materials`}>Materials</Link></p>
    </div></main>;
}

export default function App() {
  return <Routes><Route path="/" element={<Auth />} /><Route path="/courses" element={<Courses />} />
    <Route path="/courses/:id" element={<Course />} /><Route path="/courses/:id/topics" element={<TopicsSetup />} />
    <Route path="/courses/:id/materials" element={<CourseMaterials />} /></Routes>;
}
