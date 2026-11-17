"""Simulate a small class asking questions, so the instructor dashboard has something to flag.

Usage (repo root, backend running):
    backend/.venv/Scripts/python e2e/simulate_students.py JOINCODE
    backend/.venv/Scripts/python e2e/simulate_students.py JOINCODE --base http://localhost --delay 6

Each simulated student joins anonymously, asks one confused question about gradient descent,
then a follow-up (the "asked more than once" signal), and a few ask information questions.
--delay paces the requests so a free-tier LLM key is not rate limited (each question = 2 LLM calls).
"""
import argparse
import time
import httpx

CONFUSED = [
    "I don't understand why a large learning rate makes the loss blow up instead of converging faster",
    "I'm confused, why does my loss oscillate with gradient descent? I tried lowering it but I still don't get it",
    "I really don't get the learning rate, I thought bigger steps always meant faster training",
    "Gradient descent confuses me, how is the negative gradient the direction to move? I'm lost",
    "I tried SGD and my loss keeps jumping around, I don't understand why it is noisy",
    "I'm lost on momentum, I don't see how averaging past gradients helps",
]
FOLLOW_UP = "I still don't understand the learning rate part, it is confusing me"
INFO = ["What is the F1 score?", "What does high variance mean?", "What is regularisation?"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("code")
    p.add_argument("--base", default="http://localhost:8000")
    p.add_argument("--students", type=int, default=5)
    p.add_argument("--delay", type=float, default=5.0)
    a = p.parse_args()
    api = a.base.rstrip("/") + "/api/v1/student"
    with httpx.Client(timeout=60) as http:
        for i in range(a.students):
            r = http.post(f"{api}/join", json={"code": a.code.upper(), "consent": True})
            r.raise_for_status()
            headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
            questions = [CONFUSED[i % len(CONFUSED)], FOLLOW_UP]
            if i < len(INFO):
                questions.append(INFO[i])
            for q in questions:
                res = http.post(f"{api}/chat", headers=headers, json={"text": q, "session_id": f"sim-{i}"})
                status = res.status_code
                answer = res.json().get("answer", res.text)[:90] if status == 200 else res.text[:120]
                print(f"student {i + 1} [{status}] {q[:50]!r} -> {answer!r}")
                time.sleep(a.delay)
    print("\nDone. Wait ~30 s for background analysis, then open the instructor Overview page.")


if __name__ == "__main__":
    main()
