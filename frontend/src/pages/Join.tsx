import { FormEvent, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";

export default function Join() {
  const { code = "" } = useParams();
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const result = await api.join(code);
      localStorage.setItem("student_token", result.access_token);
      navigate("/student");
    } catch (err) { setError(String(err)); }
  }
  return <main className="landing"><form className="panel" onSubmit={submit}>
    <h1>Join course</h1><p>This is anonymous. Your questions are shared with the instructor only in combined form.</p>
    <label><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} required /> I consent to the data use described in the <a href="/consent">consent notice</a>.</label>
    <button className="btn p" disabled={!consent}>Join</button>{error && <p className="bad">{error}</p>}
  </form></main>;
}
