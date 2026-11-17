# Tangled: live demo script

About 12 minutes. Each step has **what to do**, **what to say**, and a **✓ check**: what you should
see, so you know it worked (use this list for your rehearsal too).
The files you need are in `e2e/samples/`.

---

## Ready-made demo data

The demo database (`backend/data/demo/`) already holds a course you can present straight away:

| What | Value |
|---|---|
| Instructor login | `lecturer@demo.tangled` / `TangledDemo2026` (local demo account only; don't reuse it on the live server) |
| Course | **Intro to Machine Learning (Week 6)**, class size 30, join code shown on its course card |
| Topics | Gradient descent, Bias-variance, Evaluation metrics, Clustering |
| Data | 5 materials, quiz results, 22 real questions from 12 anonymous students |
| Overview shows | **Gradient descent: High confidence** and **Bias-variance: Medium**, 2 topics need attention |

To create it again (after a reset, or on another machine), start the backend, then from the repo root run:
```powershell
backend\.venv\Scripts\python e2e\seed_demo.py
```
It takes about 4 minutes (every question really goes through the AI) and prints the login and join code at the end.

**Two ways to present it:**
- **Safe (recommended):** log in as the demo lecturer and show the full dashboard first (Act 4). Then show the
  student side (Act 2) by joining the same course. Nothing depends on the AI responding live except Act 2.
- **Full live story:** build a new course from scratch (Acts 1–4) and keep the seeded course as your backup.
  If anything misbehaves, switch to it: *"Here's one from a class that's been using it for a week."*

## How a student gets in

There are no student accounts or passwords. A student joins with the course's **6-character join code**, and
the browser remembers them (anonymously) from then on. Any of these works:

1. **Join link:** `http://localhost:8000/join/<CODE>`. The code is pre-filled; tick consent, then click **Join**.
2. **Type the code:** open `http://localhost:8000/join`, or click **"Are you a student? Join your course
   with a code"** on the login page, then type the code (upper- or lowercase).
3. **On a phone (same Wi-Fi):** use `http://192.168.100.171:8000/join` instead of `localhost:8000`.

Where to find the code: on the course card under **Your courses**, or **Topic setup → Course settings**.
Use an **Incognito/InPrivate** window for the student, so the instructor stays logged in in the normal
window. Each new Incognito window is a brand-new anonymous student; the same window coming back is the
same student, with their history.

## Running the class simulation from VS Code

1. Open the `tangled` folder in VS Code. Open a terminal with **Ctrl+`** (or **Terminal → New Terminal**).
   It opens at the repo root (`...\tangled>`).
2. Type the command with **your real code instead of `<CODE>`**. Don't type the angle brackets; in PowerShell
   `<` is an error. For the seeded course, for example:
   ```powershell
   backend\.venv\Scripts\python e2e\simulate_students.py NW5REV --delay 6
   ```
3. Leave it running while you talk (about 80 s). Each line shows `[200]` and the start of the answer.
4. Wait about 30 s after it ends, then press F5 on the instructor **Overview**.

Tips: increase the font with **Ctrl+=** so the audience can read it, and drag the terminal to a second
screen or split it beside the browser. If the terminal says `No such file`, you're not at the repo root:
run `cd D:\University\Projects\ai_projects\tangled` first. Running it against the seeded course adds
more students to it; against a new course, it's what makes the first topic get flagged.

---

## Before the audience arrives (10 minutes)

| ✓ | Do | Why |
|---|---|---|
| ☐ | Both servers are running: the **Tangled backend** terminal ends with `Uvicorn running on http://0.0.0.0:8000`, and the **Tangled frontend** terminal shows `Local: http://localhost:5173/` | Without them there is nothing to show |
| ☐ | Open http://localhost:8000/health/ready and check that it shows `{"ok":true}` | Confirms the database is reachable |
| ☐ | **Warm up:** register a throwaway instructor, create a course, upload one sample file, wait until it says *indexed*, then ask one question as a student. Delete that course afterwards (Topic setup, then Delete course) | The first upload loads the AI search model (10–60 s). Do it now, not in front of people |
| ☐ | On a phone on the **same Wi-Fi**, open `http://192.168.100.171:8000/health/live`. If it doesn't load, allow Python through Windows Firewall (Private networks) when Windows asks, or add the rule in Windows Security, then Firewall | Students join from their phones on this address |
| ☐ | Browser **window 1** (normal): http://localhost:8000. Browser **window 2** (Incognito): kept ready for the student. Zoom both to 125% | Two separate identities: instructor and student |
| ☐ | Keep `e2e/samples/` open in File Explorer, plus a PowerShell window at the repo root | For drag-and-drop uploads and the class simulation |

> **Which URL?** Present on **http://localhost:8000**. It is exactly how the live site runs (one server
> serving the app and the API). http://localhost:5173 is the developer view (same app, live reload). Use it
> only if you're changing code. Phones must use `http://192.168.100.171:8000`.

---

## Act 0: The problem (1 min, no clicking)

**Say:** *"In a class of 100, a lecturer finds out what students didn't understand at the exam, which is too late.
Students don't put their hands up, and office hours reach a handful of them. Tangled gives every student a tutor
that answers from the course's own materials. In the background it tells the lecturer which topics the class is
genuinely stuck on, with evidence, and without identifying any student."*

---

## Act 1: The instructor sets up a course (3 min), window 1

| Step | Do | Say | ✓ Check |
|---|---|---|---|
| 1 | Click **New to Tangled? Create an account**, then enter `demo@university.edu` / `DemoPass2026` | *"An instructor signs up in seconds."* | You land on **Your courses**, "No courses yet" |
| 2 | Create the course **Intro to Machine Learning**, class size **20** | *"Each course gets its own join code."* | A card appears with a **6-letter join code**. Write it on the whiteboard or slide |
| 3 | Open the course, then **Topic setup**. Add the topics below, **with exactly these names** (the quiz file matches on them) | *"The instructor lists the syllabus topics. That's how Tangled knows what to track."* | Each one shows "Topic added." |
| | `Gradient descent` · `Module 1` · `Learning rate, gradients and optimisation by gradient descent.` | | |
| | `Bias-variance` · `Module 2` · `Overfitting, underfitting and regularisation.` | | |
| | `Evaluation metrics` · `Module 3` · `Precision, recall, F1 and accuracy on imbalanced data.` | | |
| | `Clustering` · `Module 4` · `K-Means and DBSCAN.` | | |
| 4 | **Materials**: select all 5 good files in `e2e/samples/` (`01_…md` to `05_…ipynb`) and upload them together | *"Upload what you already have: slides, PDFs, Word, notebooks. Tangled reads and indexes them."* | Each row turns from **processing** to **indexed** within a few seconds. Kinds: Markdown, Word, PowerPoint, PDF, Notebook |
| 5 | **Quiz results**, then **Import aggregate CSV**, then `e2e/samples/quiz_good.csv` | *"Optionally import quiz results. Only totals per answer, never student names."* | "Imported 8 aggregate rows". **Gradient descent: 25%** in red; the "Hardest question" callout names it |

> The message *"Unmatched concepts: Unknown topic"* is deliberate. It shows that the import tells you
> when a quiz row doesn't match a topic.

---

## Act 2: The student experience (3 min), window 2 (Incognito) or a phone

| Step | Do | Say | ✓ Check |
|---|---|---|---|
| 6 | Open `http://localhost:8000/join/<CODE>` (on a phone, use `http://192.168.100.171:8000/join/<CODE>`) | *"Students open a link or type the code. No account, no email."* | "Joining **Intro to Machine Learning**", with the code pre-filled |
| 7 | Click the **consent notice** link, then go back. Tick the box and click **Join** | *"Students see exactly what's collected and agree before anything is stored."* | The student workspace, with **Anonymous by design** |
| 8 | Ask: `Why does a large learning rate make the loss diverge?` | *"Answers come only from the course materials, with citations, so there's no made-up content."* | An answer in about 2–5 s with superscript **[1]** and a **Sources** list naming the files |
| 9 | Ask: `Explain the learning rate trade-offs as a bullet list` | | A properly formatted bullet list, with no `**` symbols |
| 10 | Ask: `What is the capital of France?` | *"Off-syllabus questions are refused. It's a course tutor, not a general chatbot."* | "I can only answer from your course materials…", with no sources |
| 11 | Click **Still unclear** under the first answer | *"Students can say an answer didn't help. That's another signal."* | "Marked still unclear ✓" |
| 12 | Click the PDF in **Course materials** | *"Students can open the lecture notes beside the chat."* | The PDF opens in a new tab |

---

## Act 3: The class asks questions (2 min), the "aha" moment

You need several students for a topic to be flagged, which protects against false alarms. Simulate a small class.
In the PowerShell window at the repo root, run the following, using **your** join code:

```powershell
backend\.venv\Scripts\python e2e\simulate_students.py <CODE> --delay 6
```

**Say while it runs (about 80 s):** *"Here are five more students. Some are confused about the learning rate, some
just want definitions. Tangled tells these apart. 'What is the F1 score?' is a request for information, while
'I still don't get the learning rate' is confusion. One confused student is noise. A topic is flagged only
when at least 4 different students are confused **and** a second signal agrees: a low quiz score or students
coming back confused again."*

✓ Every line shows `[200]`. If you see `[429]` or `[503]`, the AI provider is rate-limiting you; just wait.
Tangled retries the analysis automatically.

Wait about 30 seconds after it finishes.

---

## Act 4: What the instructor sees (2 min), window 1

| Step | Do | Say | ✓ Check |
|---|---|---|---|
| 13 | **Overview** (press F5) | *"Instead of reading hundreds of chats, the lecturer gets one short list."* | The summary shows questions asked, students out of 20, and **1 topic needs attention**: a **Gradient descent** card marked **Review**, with the % of students and a confidence level |
| 14 | **View details** | *"Why was it flagged? Two independent signals agree: the quiz score is low, and students kept coming back."* | Two ✓ signals: *quiz correct rate below threshold* and *at least 3 students asked more than once* |
| 15 | Scroll to **What students are confused about** | *"Questions are grouped by meaning, with the student's own words highlighted, so the lecturer knows exactly what to re-teach."* | A group with an AI-written title and highlighted quotes |
| 16 | If a **Not counted: information questions** panel appears, open it | *"Plain curiosity is shown, but it isn't counted as confusion."* | Information-style questions about this topic (e.g. from Act 2) are listed. The panel is hidden when there are none, so skip it then |
| 17 | Click **Mark as addressed** | *"After re-teaching it, the lecturer closes the loop."* | The badge changes to **Addressed** |

> **Don't click "Not a real problem" during the pitch.** It removes the topic from the list. Mention it
> instead: *"If Tangled is wrong, one click dismisses it, and we use that to measure our accuracy."*

---

## Act 5: Trust and privacy (1 min)

**Say and show:**
- *"The lecturer never sees who asked what."* Point out that there are no names or IDs anywhere, and small counts show as "fewer than 5".
- *"Each student only sees their own questions; each instructor only sees their own courses."*
- **Topic setup, then Course settings**: untick *Allow new students to join*, or **Regenerate join code**. *"The lecturer controls access."*

---

## Close (30 s)

*"Every student gets a tutor grounded in the course, and every lecturer finds out what to re-teach while
there's still time to do it. It works with the files lecturers already have, and next comes plugging into
Moodle and Canvas."*

---

## If something goes wrong on stage

| Symptom | Fix |
|---|---|
| A student's answer says "The tutor is temporarily unavailable" | The AI provider hit a rate limit or is down. Wait about 20 s and ask again. Have the screenshots from your rehearsal as a backup |
| The dashboard still shows 0 topics after the simulation | Wait another 30–60 s and press F5. Analysis is retried every 30 s (watch the backend terminal for `analysis retry sweep`) |
| A file stays **processing** | Wait. The first upload loads the model; that's why you warm up |
| The phone can't open the join link | Same Wi-Fi? Firewall allowed? Otherwise show the student view in the Incognito window |
| "Invalid instructor token" after a long break | The session expired (12 h). Click **Log out** and log in again |

## Reset for another run

Stop the backend (Ctrl+C in the **Tangled backend** terminal), delete the folder `backend/data/demo/`,
then start the backend again with the same command. Your normal `backend/data/tangled.db` is never touched.

```powershell
$env:DATABASE_URL = 'sqlite:///./data/demo/tangled.db'; $env:CHROMA_DIR = './data/demo/chroma'; $env:UPLOAD_DIR = './data/demo/uploads'; .\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
(Run it from `backend/`. The frontend at :5173 is `cd frontend; npm run dev`.)
