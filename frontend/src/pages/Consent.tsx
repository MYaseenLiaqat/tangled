import { Link, useParams } from "react-router-dom";

export default function Consent() {
  const { code } = useParams();
  return <main className="landing"><section className="panel">
    <p className="eyebrow">Student consent</p>
    <h1>Before you join</h1>
    <p>By joining this course, you agree that:</p>
    <ul>
      <li>We collect the questions you type and which feedback buttons you press.</li>
      <li>We do not collect your name or email.</li>
      <li>Your instructor sees only combined results, not questions linked to your identity.</li>
      <li>Your questions are processed by an AI provider to provide answers.</li>
      <li>Contact your instructor to ask for removal of your data.</li>
    </ul>
    <Link className="btn primary" to={code ? `/join/${code}` : "/"}>Return to join</Link>
  </section></main>;
}
