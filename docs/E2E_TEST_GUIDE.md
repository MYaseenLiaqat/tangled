# Tangled: manual end-to-end test guide

This guide walks through every feature, in the order a real instructor and their students would use it.
Each step says **what to do**, **what you should see**, and **where to look** if something seems off.
Plan for about 60–90 minutes. Tick the box as you go and write anything odd in the Notes column of the
results table at the end.

Steps marked **KNOWN ISSUE** are already known to fail or to look wrong. Confirm them, but don't treat
them as new bugs.

---

## 0. Where to look

| # | Place | What it tells you |
|---|---|---|
| 1 | **The browser page** | What the user actually sees |
| 2 | **Browser DevTools (F12)**: *Network* tab, filter `api` | Each API call, its status code (200, 400, 401, 404, 429…) and its JSON response. Use it whenever the page shows an error or nothing happens |
| 3 | **DevTools, *Console* tab** | Frontend crashes and React warnings |
| 4 | **DevTools, *Application*, Local Storage** | `instructor_token`, `student_token`, `student_course_name` |
| 5 | **Backend terminal** | Startup, migrations, Python tracebacks, and one JSON log line per request (`GET /api/v1/... 200 0.123`). Analysis retries log as `analysis retry sweep retried=N` |
| 6 | **API docs**: http://localhost:8000/docs | Every endpoint; you can call them by hand |
| 7 | **Database inspector**: `e2e/inspect_db.py` | What was really stored: materials, messages, intents, failed analysis jobs |
| 8 | **Files on disk**: `backend/data/e2e/uploads/` | Uploaded files (named `<id>_<filename>`) |

---

## 1. Setup (clean, separate test database)

Use a separate data folder so this test doesn't touch your real `backend/data/tangled.db`.
Everything under `backend/data/` is already git-ignored.

**Terminal 1: backend** (PowerShell, from the repo root)
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
New-Item -ItemType Directory -Force data\e2e | Out-Null
$env:DATABASE_URL = "sqlite:///./data/e2e/tangled.db"
$env:CHROMA_DIR   = "./data/e2e/chroma"
$env:UPLOAD_DIR   = "./data/e2e/uploads"
uvicorn app.main:app --port 8000
```
Expect:
- Alembic lines ending in `Running upgrade 0006_insight_groups -> 0007_message_sources`.
- Then `Uvicorn running on http://127.0.0.1:8000`.

**Terminal 2: frontend**
```powershell
cd frontend
npm run dev
```
Expect: `Local: http://localhost:5173/`.

**Terminal 3: sample files** (repo root, run once)
```powershell
backend\.venv\Scripts\python e2e\make_samples.py
```
This writes test files to `e2e/samples/`: 5 good course files in different formats, 3 bad files, and 4 quiz CSVs.

**Quick health checks**

| ✓ | Check | Expected |
|---|---|---|
| ☐ | http://localhost:8000/health/live | `{"ok":true}` |
| ☐ | http://localhost:8000/health/ready | `{"ok":true}` (database reachable) |
| ☐ | http://localhost:8000/docs | Swagger page lists the auth, courses and student endpoints |
| ☐ | http://localhost:5173 | Tangled instructor login page |

> Use **http://localhost:5173** for sections 2–11. Section 12 tests the production setup on :8000.

---

## 2. Instructor account

| ✓ | Do | Expected | If wrong, check |
|---|---|---|---|
| ☐ | Click **New to Tangled? Create an account**. Enter email `test1@uni.edu` and password `short` | The browser blocks it: password must be at least 8 characters | |
| ☐ | Register with `test1@uni.edu` / `password123` | You land on **Your courses**, with an empty state: "No courses yet" | Network: `POST /auth/register` returns 200 |
| ☐ | Register again with the same email (after logging out, below) | Error: "Email already registered" | 409 in Network |
| ☐ | Log out: open a course later and click **Log out** in the sidebar. **KNOWN ISSUE:** there is no logout on the course list page | Back on the login page | Local Storage: `instructor_token` is gone |
| ☐ | Log in with a wrong password | "Invalid email or password" | 401 |
| ☐ | Log in correctly | Course list | |
| ☐ | Logged out, paste http://localhost:5173/courses into the address bar | Redirected to the login page (route guard) | |
| ☐ | Try 11 wrong logins within one minute | The 11th returns "Please wait before trying again." | 429 |

---

## 3. Courses

| ✓ | Do | Expected |
|---|---|---|
| ☐ | Create the course **Intro to ML** with class size **20** | A card appears showing a 6-character **join code**. Write it down |
| ☐ | Create a second course, **Scratch course**, with no class size | A second card appears |
| ☐ | Click **Intro to ML** | Course workspace opens: sidebar with Overview, Quiz results, Materials, Topic setup. Overview shows **0 questions asked** and "No topics need attention yet" |

---

## 4. Topic setup (sidebar: **Topic setup**)

The quiz CSV links quiz rows to topics **by exact name**, so use these names.

| ✓ | Do | Expected |
|---|---|---|
| ☐ | Add the topic **Gradient descent**, module `Module 1`, description `Learning rate, gradients and optimisation by gradient descent.` | "Topic added." The topic card appears, and the counter shows 1/10 |
| ☐ | Add **Bias-variance**, module `Module 2`, description `Overfitting, underfitting and regularisation.` | Added |
| ☐ | Add **Evaluation metrics**, module `Module 3`, description `Precision, recall, F1 and accuracy on imbalanced data.` | Added |
| ☐ | Add **Clustering**, module `Module 4`, description `K-Means and DBSCAN.` | Added |
| ☐ | Try a two-sentence description: `First. Second.` | Error: "Description must be one sentence" |
| ☐ | **Edit** Clustering: change the module to `Module 6` and save | "Topic updated." The card changes |
| ☐ | Add topics until you have 10. The 11th should be impossible | The **Add topic** button is disabled at 10/10. Then delete the extras, keeping the 4 topics above |
| ☐ | **Delete** a spare topic and confirm the browser dialog | "Deleted …" |

---

## 5. Materials (sidebar: **Materials**)

Upload from `e2e/samples/`. The **first** upload can take 20–60 s, because the embedding model loads (or downloads) on first use.

| ✓ | Do | Expected | If wrong, check |
|---|---|---|---|
| ☐ | Upload `01_gradient_descent.md` | A row appears with status **processing**, then turns **indexed** (the page polls every 3 s). The Sections column shows a number | `inspect_db.py`, Materials table |
| ☐ | Upload `02_bias_variance.docx`, `03_evaluation_metrics.pptx`, `04_course_summary.pdf` and `05_clustering.ipynb` together (multi-select) | All 5 files end up **indexed**, with kinds Markdown, Word, PowerPoint, PDF and Notebook | The error text under the filename |
| ☐ | Upload `bad_scanned_no_text.pdf` | Status becomes **failed**, with the reason "This PDF has no selectable text. It may be a scan." | |
| ☐ | Upload `bad_fake.pdf` | Rejected straight away: "File content does not match its extension" | 400 in Network |
| ☐ | Upload `bad_unsupported.exe`. In the file picker, choose "All files" first | "Unsupported file type: .exe" | 400 |
| ☐ | **Delete** the failed scanned PDF | The row disappears | The file is gone from `backend/data/e2e/uploads/` |
| ☐ | Look at the folder `backend/data/e2e/uploads/` | One file per material, named like `1_01_gradient_descent.md` | |

---

## 6. Quiz results (sidebar: **Quiz results**)

| ✓ | Do | Expected |
|---|---|---|
| ☐ | Before importing anything | Empty state: "No quiz results yet" |
| ☐ | **Import aggregate CSV** with `quiz_good.csv` | "Imported 8 aggregate rows. Unmatched concepts: Unknown topic." A table appears. **Gradient descent: 25% correct** is shown in red (below 60%), and its most common wrong option is **B**. The "Hardest question" callout names Gradient descent |
| ☐ | Import `quiz_bad_headers.csv` | Error about the required headers. The existing data stays unchanged |
| ☐ | Import `quiz_bad_identifiers.csv` | "Quiz CSV must not contain student identifiers" (a privacy guard) |
| ☐ | Import `quiz_bad_rows.csv` | "The CSV could not be imported. Check the headers and row numbers." The existing data stays unchanged. **KNOWN ISSUE:** the UI doesn't show *which* row failed; the Network response for the 422 does (`errors: [{row: 2, …}]`) |

The low Gradient descent quiz score is the **second signal** that the dashboard needs later on.

---

## 7. Student joining

Students need a separate browser identity. Use an **Incognito/InPrivate window** for each new student.
The student token is stored per browser; in the same browser, a student who joins again is treated as returning.

| ✓ | Do | Expected | If wrong, check |
|---|---|---|---|
| ☐ | In incognito, open `http://localhost:5173/join/<CODE>` | "Join course: Joining **Intro to ML**." The code is pre-filled | `GET /student/join/<CODE>` |
| ☐ | Click **Join** without ticking consent | "Please accept the notice to continue" | |
| ☐ | Click the **consent notice** link | The consent page lists what is collected. **Return to join** goes back with the code kept | |
| ☐ | Tick consent and click **Join** | The student workspace opens, titled with the course name, with "Anonymous by design" | Local Storage: `student_token` |
| ☐ | Open `http://localhost:5173/join/ZZZZZZ` (invalid code) in another incognito window | "Course not found" (or "That join code is invalid") | 404 |
| ☐ | Go to `http://localhost:5173/student` in a fresh incognito window without joining | Redirected to `/` (route guard) | |
| ☐ | **Returning student:** in the first student window, open the join link again and join again | You see your **previous questions** (after section 8), not an empty chat, which means the same identity was kept | `inspect_db.py`: the student count did not go up |

---

## 8. Student chat (the core experience)

Use the first student window.

| ✓ | Do | Expected | Where to check |
|---|---|---|---|
| ☐ | Course materials panel | Lists the indexed files. Only the **PDF** has a clickable link | |
| ☐ | Click the PDF | Opens inline in a new tab. **KNOWN ISSUE:** the link expires 5 minutes after the page loaded; reload the page if you get "Invalid or expired file URL" | |
| ☐ | Ask: `Why does a large learning rate make the loss diverge?` | An answer in about 2–5 s that cites `[1]`, with a **Sources** list underneath | Network: `POST /student/chat` returns 200 with `sources` |
| ☐ | Check the citation names | A PDF shows `p.1`, a PPTX `slide 1`, a DOCX its heading. **KNOWN ISSUE:** Markdown and text files show "— text" | |
| ☐ | Ask `Explain the learning rate trade-offs as a bullet list` | A real bulleted list with **bold** text; no `**` or `- ` symbols. Citations are small superscripts | |
| ☐ | Ask: `What is precision?`, then `What is DBSCAN?` | Answers grounded in the PPTX and the notebook respectively | |
| ☐ | Ask an off-topic question: `What is the capital of France?` | The refusal: "I can only answer from your course materials…". No sources | |
| ☐ | Try to send an empty question | The button stays disabled | |
| ☐ | Click **Clear** under one answer and **Still unclear** under another | "Marked clear ✓" / "Marked still unclear ✓" | `POST /student/feedback` returns 200 |
| ☐ | Reload the page (F5) | All previous Q&As, with their sources, are still there | `GET /student/messages` |
| ☐ | Follow-up: `Can you explain that more simply?` | **KNOWN ISSUE:** there is no conversation memory, so this is answered on its own or refused | |
| ☐ | Wait about 20 s, then run `e2e/inspect_db.py` | Each answered message has an intent (`confusion`, `information`, `other`), and the off-topic one has `gap`. The **Analysis jobs** rows are `done`. Anything in **Failed / pending** is usually an LLM rate limit. It is retried automatically (after 30 s, 60 s, 120 s, … up to 6 attempts), so run the inspector again a minute later and it should be `done` | Terminal 3 |

```powershell
backend\.venv\Scripts\python e2e\inspect_db.py
```

---

## 9. Instructor insights (the "aha" moment)

A topic is flagged only when **4 or more different students** are confused about it **and** either
the quiz score is below 60% or 3 or more students asked more than once. Simulating that by hand takes 5 incognito
windows, so use the simulator:

```powershell
backend\.venv\Scripts\python e2e\simulate_students.py <CODE> --students 5 --delay 6
```
Every line should show `[200]`. A `[503]` or `[429]` means the LLM provider rate-limited you; rerun with a larger `--delay`.
Wait about 30 s after it finishes.

| ✓ | Do | Expected | If wrong, check |
|---|---|---|---|
| ☐ | Instructor window: **Overview** (refresh) | Summary counts go up. **Gradient descent** appears under *Topics needing attention*, marked **Review**, with a % of students and a confidence level | `inspect_db.py`: the confusion messages are on the Gradient descent topic (`concept_id`) with confidence ≥ 0.7 |
| ☐ | Type `bias` in **Search topics** | "No topics match your search" (only flagged topics are listed) | |
| ☐ | Other topics | **KNOWN ISSUE:** topics that aren't flagged are not shown anywhere, although the API returns them | |
| ☐ | Click **View details** | The detail page loads in about 2–10 s. "Why Tangled flagged this" shows ✓ quiz correct rate below threshold and ✓ at least 3 students asked more than once. "What students are confused about" shows groups with highlighted quotes | |
| ☐ | Read the group cards | **KNOWN ISSUES:** a group title may just be a raw student question; quotes can repeat; the highlight can cut a word in the middle | |
| ☐ | Open "Not counted: information questions" | Information questions (e.g. "What is the F1 score?") are listed here and not counted as confusion | |
| ☐ | Click **Mark as addressed** | "Marked as addressed." The badge changes to **Addressed** | `inspect_db.py`, verdicts |
| ☐ | Click **Not a real problem** | "Marked as not a real problem." Back on Overview, the topic leaves the flagged list (only confusion that arrives *after* this verdict counts) | |
| ☐ | Privacy check: anywhere in the instructor UI | **No student IDs, names or per-student histories.** Counts below 5 show as "fewer than 5" | |

---

## 10. Isolation and security spot checks

| ✓ | Do | Expected |
|---|---|---|
| ☐ | Register a second instructor, `test2@uni.edu`, in another browser profile | Their course list is empty |
| ☐ | As test2, open `http://localhost:5173/courses/1/topics` (test1's course) | An error page ("Course not found"); nothing leaks |
| ☐ | Student A and student B (two incognito windows) | Each sees **only their own** questions |
| ☐ | In a student window's DevTools Console, run `fetch('/api/v1/courses',{headers:{Authorization:'Bearer '+localStorage.student_token}}).then(r=>r.status)` | `401`: a student token can't reach the instructor API |
| ☐ | In a student window, join the **Scratch course** code | A new anonymous identity for that course. Questions there use only Scratch course materials (none yet, so you get the refusal) |

---

## 11. Course settings and deletion (sidebar: **Topic setup**, Course settings panel)

| ✓ | Do | Expected |
|---|---|---|
| ☐ | Change the class size to 30 and **Save settings** | "Course settings saved." On Overview, the "x of 30" figure updates |
| ☐ | Untick **Allow new students to join** and save. Open the join link in a fresh incognito window | "Joining is closed for this course." and the Join button is disabled |
| ☐ | Existing student window | Can still ask questions (closing only blocks *new* joins). Re-open joining afterwards |
| ☐ | **Regenerate join code** | A new code is shown. The old `/join/<OLD>` link now says the course was not found |
| ☐ | **Delete course** on *Scratch course*: type the name wrongly at the prompt | "Type the course name exactly to confirm deletion". The course still exists |
| ☐ | Delete it again, typing the name correctly | Redirected to Your courses, and the course is gone. `inspect_db.py` shows no rows for it, and its upload files are removed |

---

## 12. Production mode (how it will run when live)

In production, FastAPI serves the built frontend itself on port 8000; there's no Vite.

```powershell
cd frontend; npm run build; cd ..
```
Restart Terminal 1's `uvicorn` (it only finds `frontend/dist` at startup), then open **http://localhost:8000**.

| ✓ | Do | Expected |
|---|---|---|
| ☐ | Log in at http://localhost:8000, then click through the course | Works (navigating inside the app) |
| ☐ | Open `http://localhost:8000/join/<CODE>` directly, and press F5 on inner pages (`/student`, `/courses/1/topics`) | The app loads every time, not `{"detail":"Not Found"}` |
| ☐ | Open `http://localhost:8000/api/v1/nope` and `http://localhost:8000/assets/nope.js` | Still a 404 (only page routes fall back to the app) |
| ☐ | Docker (if installed): copy `backend/.env.example` to `backend/.env` with real values, then run `docker compose up --build` and open http://localhost | The same app on port 80. Test the join link there too |

---

## 13. Mobile (students will mostly use phones)

DevTools, then the device toolbar (Ctrl+Shift+M), then *iPhone 12* or similar:

| ✓ | Page | Expected |
|---|---|---|
| ☐ | Join page | Fits the screen; checkbox and button are easy to tap |
| ☐ | Student workspace | No sideways scrolling. The question box is usable and answers are readable |
| ☐ | Instructor Overview | Usable. The sidebar shouldn't cover the content |

---

## 14. Automated suites (run last)

```powershell
cd backend; .\.venv\Scripts\python -m pytest -q        # expect 44 passed
cd ..\frontend; npm run test                           # expect 10 passed
npm run build                                          # expect "built in …"
```

---

## 15. Clean up

Stop both servers, then delete `backend/data/e2e/` to discard all test data. Your real data in `backend/data/tangled.db` was never touched.

---

## Known issues (already found during the 2026-11-16 audit)

| # | Severity | Issue | Seen in step |
|---|---|---|---|
| 1 | ~~Blocker~~ **Fixed 2026-11-17** | Deep links and refreshes gave a 404 when served from FastAPI or Docker | 12 |
| 2 | ~~Blocker~~ **Fixed 2026-11-17** | `JWT_SECRET` was the value committed in `.env.example`. Rotated locally and blanked in the example. **Use a new secret on the server too** | n/a |
| 3 | ~~Blocker~~ **Fixed 2026-11-17** | Analyses that hit LLM rate limits are now retried automatically with backoff | 8, 9 |
| 4 | ~~High~~ **Fixed 2026-11-17** | Student answers showed raw markdown | 8 |
| 5 | Medium | Topics that aren't flagged are hidden; the dashboard looks empty until 4+ students are confused | 9 |
| 6 | Medium | No landing page; no copyable full join URL or QR code | 3, 11 |
| 7 | ~~Medium~~ **Fixed 2026-11-17** | App and request logs were silenced at startup | 0 |
| 8 | Low | Markdown and text citations say "text"; no chat memory; PDF link expires after 5 minutes; group title, duplicate quote and highlight glitches; no logout on the course list; login rate limit is shared by everyone behind nginx | 2, 8, 9 |

## Results

| Section | Pass / Fail | Notes |
|---|---|---|
| 1 Setup | | |
| 2 Instructor account | | |
| 3 Courses | | |
| 4 Topics | | |
| 5 Materials | | |
| 6 Quiz | | |
| 7 Joining | | |
| 8 Student chat | | |
| 9 Insights | | |
| 10 Isolation | | |
| 11 Settings and deletion | | |
| 12 Production mode | | |
| 13 Mobile | | |
| 14 Automated suites | | |
