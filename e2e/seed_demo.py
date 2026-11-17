"""Fill a running Tangled server with a ready-to-present demo course.

Everything goes through the real API, so materials are really indexed and every question is really
answered and analysed by the LLM. Takes about 4 minutes and ~60 small LLM calls.

Usage (repo root, backend running):
    backend/.venv/Scripts/python e2e/seed_demo.py
    backend/.venv/Scripts/python e2e/seed_demo.py --base http://localhost:8000

What you get, as the demo instructor below:
  * "Intro to Machine Learning (Week 6)", class size 30, 4 topics, 5 materials, quiz results
  * 11 anonymous students and 22 questions, so the Overview shows:
      - Gradient descent  -> flagged, High confidence (low quiz score + students asking again)
      - Bias-variance     -> flagged, Medium (several students came back still confused)
      - Evaluation metrics, Clustering -> mostly information questions, so not flagged
  * The course's join code is printed at the end. Join with it to show the student view live.

Rerunning creates another copy of the course (the instructor account is reused).
"""
import argparse
import sys
import time
from pathlib import Path

import httpx

# Test account for the local demo only. Never reuse these values on a live server.
INSTRUCTOR_EMAIL = "lecturer@demo.tangled"
INSTRUCTOR_PASSWORD = "TangledDemo2026"
COURSE = "Intro to Machine Learning (Week 6)"
SAMPLES = Path(__file__).parent / "samples"
FILES = ["01_gradient_descent.md", "02_bias_variance.docx", "03_evaluation_metrics.pptx",
         "04_course_summary.pdf", "05_clustering.ipynb"]
TOPICS = [("Gradient descent", "Module 1 · Optimisation", "Learning rate, gradients and optimisation by gradient descent."),
          ("Bias-variance", "Module 2 · Generalisation", "Overfitting, underfitting and regularisation."),
          ("Evaluation metrics", "Module 3 · Model evaluation", "Precision, recall, F1 and accuracy on imbalanced data."),
          ("Clustering", "Module 4 · Unsupervised learning", "K-Means and DBSCAN.")]

# One list per anonymous student; each student asks their questions in order.
STUDENTS = [
    ["I don't understand why a large learning rate makes the loss blow up instead of converging faster",
     "I still don't get the learning rate part, I lowered it and now training barely moves"],
    ["I'm confused, why does my loss oscillate with gradient descent? I tried a smaller step and I still don't get it",
     "Sorry, I'm still lost on how to choose a learning rate"],
    ["I really don't get the learning rate, I thought bigger steps always meant faster training",
     "What is the F1 score?"],
    ["Gradient descent confuses me, how is the negative gradient the direction to move? I'm lost",
     "I still don't understand why we move against the gradient"],
    ["I tried SGD and my loss keeps jumping around, I don't understand why it is so noisy",
     "What does momentum do?"],
    ["I don't understand the difference between gradient descent and stochastic gradient descent, they look the same to me"],
    ["I don't understand overfitting, my training error is low so why is the model bad?",
     "I'm still confused, how can low training error be a bad sign?"],
    ["I'm confused about bias versus variance, which one means the model is too simple?",
     "I still mix up high bias and high variance, I keep getting them the wrong way round"],
    ["I don't get why regularisation helps, isn't a penalty just making the model worse?",
     "Still confused, why would dropout reduce overfitting instead of hurting accuracy?"],
    ["I'm struggling to understand underfitting, what does it look like in practice?",
     "What is precision?"],
    ["What is recall?", "What is DBSCAN?", "How does K-Means choose its clusters?"],
]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://localhost:8000")
    p.add_argument("--delay", type=float, default=4.0, help="seconds between questions (free-tier LLM limits)")
    a = p.parse_args()
    api = a.base.rstrip("/") + "/api/v1"
    h = httpx.Client(timeout=90)
    try:
        h.get(a.base.rstrip("/") + "/health/ready").raise_for_status()
    except httpx.HTTPError:
        print(f"The backend is not reachable at {a.base}. Start it first.")
        return 2

    creds = {"email": INSTRUCTOR_EMAIL, "password": INSTRUCTOR_PASSWORD}
    r = h.post(api + "/auth/login", json=creds)
    if r.status_code != 200:
        r = h.post(api + "/auth/register", json=creds)
    r.raise_for_status()
    H = {"Authorization": f"Bearer {r.json()['access_token']}"}

    course = h.post(api + "/courses", headers=H, json={"name": COURSE, "class_size": 30}).json()
    cid, code = course["id"], course["join_code"]
    print(f"Course created: {COURSE} (join code {code})")
    for name, module, description in TOPICS:
        h.post(f"{api}/courses/{cid}/topics", headers=H,
               json={"name": name, "module_label": module, "description": description}).raise_for_status()
    print("Topics added")

    h.post(f"{api}/courses/{cid}/materials", headers=H,
           files=[("files", (name, (SAMPLES / name).read_bytes())) for name in FILES]).raise_for_status()
    for _ in range(80):
        materials = h.get(f"{api}/courses/{cid}/materials", headers=H).json()
        if all(m["status"] != "processing" for m in materials):
            break
        time.sleep(3)
    failed = [m["filename"] for m in materials if m["status"] != "indexed"]
    print("Materials indexed" if not failed else f"WARNING: not indexed: {failed}")

    h.post(f"{api}/courses/{cid}/quiz/import", headers=H,
           files={"file": ("quiz.csv", (SAMPLES / "quiz_good.csv").read_bytes())}).raise_for_status()
    print("Quiz results imported")

    total = sum(len(questions) for questions in STUDENTS)
    asked = errors = 0
    print(f"Students asking {total} questions (about {total * (a.delay + 2) / 60:.0f} min)...")
    for i, questions in enumerate(STUDENTS, start=1):
        joined = h.post(api + "/student/join", json={"code": code, "consent": True})
        joined.raise_for_status()
        S = {"Authorization": f"Bearer {joined.json()['access_token']}"}
        for question in questions:
            for attempt in range(4):  # the LLM provider may rate-limit a burst: back off and retry
                res = h.post(api + "/student/chat", headers=S, json={"text": question, "session_id": f"seed-{i}"})
                if res.status_code not in (429, 503):
                    break
                time.sleep(10 * (attempt + 1))
            asked += 1
            if res.status_code == 200:
                if "still" in question.lower():
                    h.post(api + "/student/feedback", headers=S,
                           json={"message_id": res.json()["message_id"], "value": "unclear"})
            else:
                errors += 1
                print(f"   student {i}: [{res.status_code}] {question[:50]!r}")
            print(f"   {asked}/{total}", end="\r")
            time.sleep(a.delay)
    print(f"   {asked - errors}/{total} questions answered" + (f", {errors} failed (rate limit?)" if errors else ""))

    print("Waiting for background analysis...")
    flagged = []
    for _ in range(12):
        time.sleep(15)
        insights = h.get(f"{api}/courses/{cid}/insights", headers=H).json()
        flagged = [(t["name"], t["confidence"]) for t in insights["flagged"]]
        if len(flagged) >= 2:
            break
    print(f"Overview: {insights['summary']}")
    print(f"Flagged topics: {flagged or 'none yet (analysis retries every 30 s; refresh in a minute)'}")
    print("\nReady to present:")
    print(f"  Instructor login : {a.base}  ->  {INSTRUCTOR_EMAIL} / {INSTRUCTOR_PASSWORD}")
    print(f"  Student join link: {a.base}/join/{code}   (or open {a.base}/join and type {code})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
