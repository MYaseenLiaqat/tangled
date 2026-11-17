import { Link, useParams } from "react-router-dom";
import { Brand } from "../ui/Brand";

export default function Consent() {
  const { code } = useParams();
  return <main className="auth">
    <div className="auth-top"><Brand /></div>
    <section className="auth-card reading" style={{ width: "min(100%, 560px)" }}>
      <p className="eyebrow">Student consent</p>
      <h1>Before you join</h1>
      <p className="lead">By joining this course, you agree that:</p>
      <ul>
        <li>We collect the questions you type and which feedback buttons you press.</li>
        <li>We do not collect your name or email.</li>
        <li>Your instructor sees only combined results, not questions linked to your identity.</li>
        <li>Your questions are processed by an AI provider to provide answers.</li>
        <li>Contact your instructor to ask for removal of your data.</li>
      </ul>
      <Link className="btn btn-primary btn-lg btn-block" to={code ? `/join/${code}` : "/join"}>Return to join</Link>
    </section>
  </main>;
}
