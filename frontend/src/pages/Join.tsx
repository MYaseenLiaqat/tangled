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
      navigate("/student");
    } catch (err) { setError(friendlyError(err, "We could not join that course. Check the code and try again.")); checkbox.current?.focus(); }
  }
  return <main className="landing"><form className="panel" onSubmit={submit}>
    <h1>Join course</h1>{course && <p>Joining <b>{course.name}</b>.</p>}<p>This is anonymous. Your questions are shared with the instructor only in combined form.</p>
    <label>Course code<input value={joinCode} maxLength={6} onChange={e => setJoinCode(e.target.value.toUpperCase())} /></label>
    <label><input ref={checkbox} type="checkbox" checked={consent} onChange={e => { setConsent(e.target.checked); if (e.target.checked) setError(""); }} /> I consent to the data use described in the <a href="/consent">consent notice</a>.</label>
    {error && <p className="bad" role="alert">{error}</p>}
    <button className="btn p">Join</button>
  </form></main>;
}
