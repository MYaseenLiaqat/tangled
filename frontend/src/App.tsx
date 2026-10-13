import { useState } from "react";
import { NavLink, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { api } from "./api";
import Topics from "./pages/Topics";
import TopicDetail from "./pages/TopicDetail";
import Materials from "./pages/Materials";
import Quiz from "./pages/Quiz";
import Integrations from "./pages/Integrations";
import Student from "./pages/Student";

function Landing() {
  const nav = useNavigate();
  const [tok, setTok] = useState(""); const [code, setCode] = useState(""); const [err, setErr] = useState("");
  return (
    <div className="landing">
      <h1>Tangled</h1><p className="mute">Find out what your class finds confusing, without asking one by one.</p>
      <div className="cols">
        <div className="panel"><h3>Instructor</h3><input placeholder="Teacher token" type="password" value={tok} onChange={e => setTok(e.target.value)} />
          <button className="btn p" onClick={async () => { localStorage.setItem("teacher", tok); try { await api.topics(); nav("/teacher"); } catch { setErr("Invalid teacher token"); } }}>Open dashboard</button></div>
        <div className="panel"><h3>Student</h3><input placeholder="Your student code" value={code} onChange={e => setCode(e.target.value.trim())} />
          <button className="btn p" onClick={async () => { localStorage.setItem("code", code); try { await api.login(code); nav("/student"); } catch { setErr("Unknown student code"); } }}>Open my course</button></div>
      </div>{err && <p className="bad">{err}</p>}
    </div>);
}

function TeacherShell() {
  return (
    <div className="shell"><aside className="side"><div className="logo">Tangled</div>
      <NavLink end to="/teacher">Topics</NavLink><NavLink to="/teacher/materials">Course materials</NavLink>
      <NavLink to="/teacher/quiz">Quiz results</NavLink><NavLink to="/teacher/integrations">Integrations</NavLink></aside>
      <main><Outlet /></main></div>);
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/teacher" element={<TeacherShell />}>
        <Route index element={<Topics />} /><Route path="topics/:id" element={<TopicDetail />} />
        <Route path="materials" element={<Materials />} /><Route path="quiz" element={<Quiz />} /><Route path="integrations" element={<Integrations />} />
      </Route>
      <Route path="/student" element={<Student />} />
    </Routes>);
}
