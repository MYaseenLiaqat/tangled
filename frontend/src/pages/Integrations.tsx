export default function Integrations() {
  const snippet = `<script src="https://YOUR-HOST/widget.js"\n  data-course="ai-ml-deep-learning"\n  data-student-id="{{ anonymous_user_id }}"\n  data-key="pk_live_xxxxxxxx" async></script>`;
  return (<>
    <h1>Connect to your learning platform</h1><p className="mute">Planned for after the pilot. The pilot uses the student app in this project.</p>
    <div className="panel"><h3>Embed snippet (planned)</h3><pre>{snippet}</pre></div>
    <div className="panel"><table><thead><tr><th>Platform</th><th>Method</th><th>Status</th></tr></thead><tbody>
      <tr><td>Any platform that allows custom HTML</td><td>Embed widget</td><td><span className="tag mon">Planned</span></td></tr>
      <tr><td>Moodle, Canvas, Blackboard</td><td>LTI 1.3 sign-in</td><td><span className="tag mon">Planned</span></td></tr>
      <tr><td>Other systems</td><td>REST API (see /docs)</td><td><span className="tag ok">Available</span></td></tr></tbody></table></div>
    <p className="note">Your platform sends an anonymous student ID. Tangled never receives names or email addresses.</p>
  </>);
}
