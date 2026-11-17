import { FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { friendlyError } from "../utils/errors";

export default function Join() {
  const { code = "" } = useParams();
  const [joinCode, setJoinCode] = useState(code.toUpperCase());
  const [course, setCourse] = useState<any>();
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");
  const checkbox = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  useEffect(() => {
    setJoinCode(code.toUpperCase());
    if (code) api.joinInfo(code).then(setCourse).catch(err => setError(friendlyError(err, "That join code is invalid.")));
  }, [code]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!joinCode.trim()) {
      setError("Enter a course code.");
      checkbox.current?.focus();
      return;
    }
    if (!consent) {
      setError("Please accept the notice to continue");
      checkbox.current?.focus();
      return;
    }
    try {
      const result = await api.join(joinCode.trim());
      localStorage.setItem("student_token", result.access_token);
      localStorage.setItem("student_course_name", result.course_name);
      navigate("/student");
    } catch (err) { setError(friendlyError(err, "We could not join that course. Check the code and try again.")); checkbox.current?.focus(); }
  }
  const closed = course && !course.joining_open;
  return <main className="auth-page">
    <div className="auth-brand"><span className="brand-mark">t</span><span>Tangled</span></div>
    <section className="auth-card"><p className="eyebrow">Student access</p>
      <h1>Join course</h1>
      <p className="lead">{course ? <>Joining <b>{course.name}</b>.</> : "Enter the 6-character code from your instructor."}</p>
      {closed && <p className="error" role="alert">Joining is closed for this course.</p>}
      <form className="form" onSubmit={submit}>
        <label>Course code<input className="code-input" value={joinCode} maxLength={6} autoComplete="off" autoCapitalize="characters" placeholder="ABC123" onChange={e => setJoinCode(e.target.value.toUpperCase())} /></label>
        <label className="consent-check"><input ref={checkbox} type="checkbox" checked={consent} onChange={e => { setConsent(e.target.checked); if (e.target.checked) setError(""); }} /><span>I consent to the data use described in the <a href={`/consent/${joinCode}`}>consent notice</a>.</span></label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn primary btn-block" disabled={Boolean(closed)}>Join</button>
      </form>
      <p className="note">No account needed. You stay anonymous: your instructor only sees questions combined with other students'.</p>
    </section>
  </main>;
}
