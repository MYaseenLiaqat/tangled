"""Automated API walk-through of docs/E2E_TEST_GUIDE.md (sections 1-12), against a running backend.

It does through the API what the guide asks you to do in the browser, and prints PASS/FAIL per step.
It uses the real LLM, so it costs a few dozen small requests. Run it on a fresh test database.

Usage (repo root, backend running, sample files present):
    backend/.venv/Scripts/python e2e/api_smoke.py                       # http://localhost:8000
    backend/.venv/Scripts/python e2e/api_smoke.py --base http://localhost --skip-class

--skip-class skips the simulated class (section 9), which needs ~2 minutes and ~40 LLM calls.
Exit code is 0 only when every step passed.
"""
import argparse
import sys
import time
import uuid
from pathlib import Path

import httpx

SAMPLES = Path(__file__).parent / "samples"
GOOD = ["01_gradient_descent.md", "02_bias_variance.docx", "03_evaluation_metrics.pptx",
        "04_course_summary.pdf", "05_clustering.ipynb"]
TOPICS = [("Gradient descent", "Module 1", "Learning rate, gradients and optimisation by gradient descent."),
          ("Bias-variance", "Module 2", "Overfitting, underfitting and regularisation."),
          ("Evaluation metrics", "Module 3", "Precision, recall, F1 and accuracy on imbalanced data."),
          ("Clustering", "Module 4", "K-Means and DBSCAN.")]
CONFUSED = [
    "I don't understand why a large learning rate makes the loss blow up instead of converging faster",
    "I'm confused, why does my loss oscillate with gradient descent? I tried lowering it but I still don't get it",
    "I really don't get the learning rate, I thought bigger steps always meant faster training",
    "Gradient descent confuses me, how is the negative gradient the direction to move? I'm lost",
    "I tried SGD and my loss keeps jumping around, I don't understand why it is noisy",
]
FOLLOW_UP = "I still don't understand the learning rate part, it is confusing me"

results: list[tuple[str, bool]] = []


def check(name: str, ok, detail="") -> bool:
    results.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (f"   -> {str(detail)[:200]}" if detail and not ok else ""))
    return bool(ok)


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def upload(h, api, cid, H, *names):
    return h.post(f"{api}/courses/{cid}/materials", headers=H,
                  files=[("files", (n, (SAMPLES / n).read_bytes())) for n in names])


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://localhost:8000")
    p.add_argument("--skip-class", action="store_true")
    p.add_argument("--delay", type=float, default=5.0, help="seconds between chat calls (free-tier LLM limits)")
    a = p.parse_args()
    if not (SAMPLES / GOOD[0]).exists():
        print("Sample files missing: run e2e/make_samples.py first.")
        return 2
    base = a.base.rstrip("/")
    api = base + "/api/v1"
    h = httpx.Client(timeout=90)
    run = uuid.uuid4().hex[:6]
    email1, email2 = f"smoke1-{run}@uni.edu", f"smoke2-{run}@uni.edu"

    print("== 1 Health")
    check("live", h.get(base + "/health/live").status_code == 200)
    check("ready", h.get(base + "/health/ready").status_code == 200)
    check("API docs", h.get(base + "/docs").status_code == 200)

    print("== 2 Instructor account")
    check("short password rejected", h.post(api + "/auth/register", json={"email": email1, "password": "short"}).status_code == 422)
    r = h.post(api + "/auth/register", json={"email": email1, "password": "password123"})
    if not check("register", r.status_code == 200, r.text):
        return 1
    H = bearer(r.json()["access_token"])
    r = h.post(api + "/auth/register", json={"email": email1, "password": "password123"})
    check("duplicate email -> 409", r.status_code == 409, r.text)
    r = h.post(api + "/auth/login", json={"email": email1, "password": "wrongpass1"})
    check("wrong password -> 401", r.status_code == 401, r.text)
    check("login", h.post(api + "/auth/login", json={"email": email1, "password": "password123"}).status_code == 200)

    print("== 3 Courses")
    course = h.post(api + "/courses", headers=H, json={"name": "Intro to ML", "class_size": 20}).json()
    cid, code = course["id"], course["join_code"]
    check("join code is 6 characters", len(code) == 6, code)
    scratch = h.post(api + "/courses", headers=H, json={"name": "Scratch course"}).json()
    check("two courses listed", len(h.get(api + "/courses", headers=H).json()) == 2)
    check("empty overview", h.get(f"{api}/courses/{cid}/insights", headers=H).json()["flagged"] == [])

    print("== 4 Topics")
    ids = {}
    for name, module, desc in TOPICS:
        r = h.post(f"{api}/courses/{cid}/topics", headers=H, json={"name": name, "module_label": module, "description": desc})
        check(f"add topic {name}", r.status_code == 200, r.text)
        ids[name] = r.json().get("id")
    r = h.post(f"{api}/courses/{cid}/topics", headers=H, json={"name": "X", "module_label": "M", "description": "First. Second."})
    check("two-sentence description rejected", r.status_code == 422 and "one sentence" in r.text, r.text)
    r = h.patch(f"{api}/courses/{cid}/topics/{ids['Clustering']}", headers=H, json={"module_label": "Module 6"})
    check("edit topic", r.status_code == 200 and r.json()["module_label"] == "Module 6", r.text)
    spare = [h.post(f"{api}/courses/{cid}/topics", headers=H,
                    json={"name": f"Spare {i}", "module_label": "M", "description": "Spare."}).json()["id"] for i in range(6)]
    r = h.post(f"{api}/courses/{cid}/topics", headers=H, json={"name": "Eleventh", "module_label": "M", "description": "No."})
    check("11th topic blocked", r.status_code == 400, r.text)
    for topic_id in spare:
        h.delete(f"{api}/courses/{cid}/topics/{topic_id}", headers=H)
    check("delete topics (back to 4)", len(h.get(f"{api}/courses/{cid}/topic-list", headers=H).json()) == 4)

    print("== 5 Materials (first upload may take up to a minute while the embedding model loads)")
    check("upload Markdown", upload(h, api, cid, H, GOOD[0]).status_code == 200)
    check("upload 4 files at once", upload(h, api, cid, H, *GOOD[1:]).status_code == 200)
    r = upload(h, api, cid, H, "bad_scanned_no_text.pdf")
    scanned = r.json()[0]["id"] if r.status_code == 200 else None
    r = upload(h, api, cid, H, "bad_fake.pdf")
    check("fake PDF rejected", r.status_code == 400 and "does not match" in r.text, r.text)
    r = upload(h, api, cid, H, "bad_unsupported.exe")
    check(".exe rejected", r.status_code == 400 and "Unsupported" in r.text, r.text)
    started = time.time()
    while time.time() - started < 240:
        mats = h.get(f"{api}/courses/{cid}/materials", headers=H).json()
        if all(m["status"] != "processing" for m in mats):
            break
        time.sleep(3)
    print(f"   indexing finished in {time.time() - started:.0f}s")
    for m in mats:
        print(f"   {m['filename']:<28} {m['kind']:<11} {m['status']:<9} sections={m['chunks']} {m['error'][:60]}")
    good = [m for m in mats if m["filename"] in GOOD]
    check("all 5 good files indexed", len(good) == 5 and all(m["status"] == "indexed" for m in good))
    bad = [m for m in mats if m["id"] == scanned]
    check("scanned PDF failed with a reason", bad and bad[0]["status"] == "failed" and "scan" in bad[0]["error"], bad)
    check("delete material", scanned and h.delete(f"{api}/courses/{cid}/materials/{scanned}", headers=H).status_code == 200)

    print("== 6 Quiz")
    check("quiz empty before import", h.get(f"{api}/courses/{cid}/quiz", headers=H).json() == [])
    r = h.post(f"{api}/courses/{cid}/quiz/import", headers=H, files={"file": ("q.csv", (SAMPLES / "quiz_good.csv").read_bytes())})
    check("good CSV: 8 rows, 'Unknown topic' unmatched", r.status_code == 200 and r.json()["imported"] == 8
          and r.json()["unmatched_concepts"], r.text)
    quiz = {row["topic"]: row for row in h.get(f"{api}/courses/{cid}/quiz", headers=H).json()}
    gd = quiz.get("Gradient descent", {})
    check("Gradient descent 25% correct, top wrong B", gd.get("correct_rate") == 0.25 and gd.get("top_wrong") == "B", gd)
    for name, needle in [("quiz_bad_headers.csv", "headers"), ("quiz_bad_identifiers.csv", "identifiers"),
                         ("quiz_bad_rows.csv", "errors")]:
        r = h.post(f"{api}/courses/{cid}/quiz/import", headers=H, files={"file": (name, (SAMPLES / name).read_bytes())})
        check(f"{name} rejected", r.status_code in (400, 422) and needle in r.text, r.text)
    check("existing quiz data unchanged", len(h.get(f"{api}/courses/{cid}/quiz", headers=H).json()) == 4)

    print("== 7 Joining")
    check("join info shows course", h.get(f"{api}/student/join/{code}").json().get("name") == "Intro to ML")
    check("join without consent -> 400", h.post(api + "/student/join", json={"code": code, "consent": False}).status_code == 400)
    r = h.post(api + "/student/join", json={"code": code, "consent": True})
    check("join", r.status_code == 200, r.text)
    student = r.json()["access_token"]
    S = bearer(student)
    check("invalid code -> 404", h.get(f"{api}/student/join/ZZZZZZ").status_code == 404)

    print("== 8 Student chat")
    mats = h.get(api + "/student/materials", headers=S).json()
    pdf = [m for m in mats if m["kind"] == "PDF"]
    check("only the PDF has a link", pdf and pdf[0]["file_url"] and all(not m["file_url"] for m in mats if m["kind"] != "PDF"))
    if pdf:
        r = h.get(base + pdf[0]["file_url"])
        check("PDF opens", r.status_code == 200 and r.content.startswith(b"%PDF"), r.status_code)
    message_ids, last = [], {}
    for q in ["Why does a large learning rate make the loss diverge?", "Explain the learning rate trade-offs as a bullet list",
              "What is precision?", "What is DBSCAN?", "What is the capital of France?"]:
        t0 = time.time()
        r = h.post(api + "/student/chat", headers=S, json={"text": q, "session_id": "smoke"})
        last = r.json() if r.status_code == 200 else {}
        sources = [f"{s.get('material')} {s.get('section')}" for s in last.get("sources", [])][:2]
        print(f"   [{r.status_code}] {time.time() - t0:.1f}s {q!r}\n         -> {last.get('answer', r.text)[:100]!r} {sources}")
        if check(f"chat: {q[:40]}", r.status_code == 200, r.text):
            message_ids.append(last["message_id"])
        time.sleep(a.delay)
    check("off-topic question refused, no sources", "only answer from your course materials" in last.get("answer", "")
          and not last.get("sources"))
    check("empty question rejected", h.post(api + "/student/chat", headers=S, json={"text": ""}).status_code == 422)
    if len(message_ids) >= 2:
        check("feedback: clear", h.post(api + "/student/feedback", headers=S, json={"message_id": message_ids[0], "value": "clear"}).status_code == 200)
        check("feedback: still unclear", h.post(api + "/student/feedback", headers=S, json={"message_id": message_ids[1], "value": "unclear"}).status_code == 200)
    history = h.get(api + "/student/messages", headers=S).json()
    check("history survives reload, with sources and feedback", len(history) == 5 and history[0]["sources"]
          and history[0]["feedback"] == "clear")
    r = h.post(api + "/student/join", headers=S, json={"code": code, "consent": True})
    check("returning student keeps the same identity", r.json().get("access_token") == student)

    print("== 10 Isolation")
    other = bearer(h.post(api + "/auth/register", json={"email": email2, "password": "password123"}).json()["access_token"])
    check("second instructor sees no courses", h.get(api + "/courses", headers=other).json() == [])
    check("second instructor cannot open first's course", h.get(f"{api}/courses/{cid}/insights", headers=other).status_code == 404)
    check("student token cannot use instructor API", h.get(api + "/courses", headers=S).status_code == 401)
    student_b = bearer(h.post(api + "/student/join", json={"code": code, "consent": True}).json()["access_token"])
    check("student B sees only their own messages", h.get(api + "/student/messages", headers=student_b).json() == [])

    if not a.skip_class:
        print("== 9 Insights (simulating 5 confused students; ~2 minutes)")
        for i, question in enumerate(CONFUSED):
            token = bearer(h.post(api + "/student/join", json={"code": code, "consent": True}).json()["access_token"])
            for q in (question, FOLLOW_UP):
                r = h.post(api + "/student/chat", headers=token, json={"text": q, "session_id": f"sim-{i}"})
                check(f"student {i + 1} asks", r.status_code == 200, r.text)
                time.sleep(a.delay)
        print("   waiting 40 s for background analysis...")
        time.sleep(40)
        insights = h.get(f"{api}/courses/{cid}/insights", headers=H).json()
        print(f"   summary: {insights['summary']}")
        flagged = {t["name"]: t for t in insights["flagged"]}
        print(f"   flagged: {list(flagged)}")
        topic = flagged.get("Gradient descent")
        check("Gradient descent is flagged", topic, list(flagged))
        check("no other topic is flagged", set(flagged) <= {"Gradient descent"}, list(flagged))
        if topic:
            detail = h.get(f"{api}/courses/{cid}/topics/{topic['id']}/insights", headers=H).json()
            print(f"   signals: {detail['signals']}; groups: {[g['title'] for g in detail['groups']]}")
            check("both signals present", len(detail["signals"]) == 2, detail["signals"])
            h.post(f"{api}/courses/{cid}/topics/{topic['id']}/verdict", headers=H, json={"verdict": "addressed"})
            now = {t["id"]: t for t in h.get(f"{api}/courses/{cid}/insights", headers=H).json()["flagged"]}
            check("Mark as addressed -> status addressed", now.get(topic["id"], {}).get("status") == "addressed")
            h.post(f"{api}/courses/{cid}/topics/{topic['id']}/verdict", headers=H, json={"verdict": "false_alarm"})
            now = {t["id"] for t in h.get(f"{api}/courses/{cid}/insights", headers=H).json()["flagged"]}
            check("Not a real problem -> leaves flagged list", topic["id"] not in now)

    print("== 11 Settings and deletion")
    check("class size saved", h.patch(f"{api}/courses/{cid}", headers=H, json={"class_size": 30}).json()["class_size"] == 30)
    h.patch(f"{api}/courses/{cid}", headers=H, json={"joining_open": False})
    check("closed: join page says closed", h.get(f"{api}/student/join/{code}").json()["joining_open"] is False)
    check("closed: new join -> 403", h.post(api + "/student/join", json={"code": code, "consent": True}).status_code == 403)
    check("closed: existing student can still ask", h.post(api + "/student/chat", headers=S,
                                                         json={"text": "What is recall?"}).status_code == 200)
    h.patch(f"{api}/courses/{cid}", headers=H, json={"joining_open": True})
    new_code = h.post(f"{api}/courses/{cid}/join-code/regenerate", headers=H).json()["join_code"]
    check("regenerated code works, old one 404s", new_code != code and h.get(f"{api}/student/join/{code}").status_code == 404)
    r = h.request("DELETE", f"{api}/courses/{scratch['id']}", headers=H, json={"confirmation": "wrong"})
    check("delete with wrong name refused", r.status_code == 400, r.text)
    r = h.request("DELETE", f"{api}/courses/{scratch['id']}", headers=H, json={"confirmation": "Scratch course"})
    check("delete course", r.status_code == 200 and len(h.get(api + "/courses", headers=H).json()) == 1, r.text)

    print("== 12 Production page routes (needs frontend/dist built before the backend started)")
    for page in ["/", f"/join/{new_code}", "/student", f"/courses/{cid}/topics"]:
        r = h.get(base + page)
        check(f"page {page} serves the app", r.status_code == 200 and 'id="root"' in r.text, r.status_code)
    check("unknown API path still 404", h.get(api + "/nope").status_code == 404)
    check("missing asset still 404", h.get(base + "/assets/nope.js").status_code == 404)

    failed = [name for name, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    for name in failed:
        print("   FAILED:", name)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
