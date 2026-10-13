# Phase 4: Student join and chat (F5, F6)
Read `.github/copilot-instructions.md` and `docs/SCOPE.md`. Build ONLY F5 and F6.

Join: `/join/:code` page shows the course name and a consent notice (text in `docs/CONSENT.md`, create it from this outline: what is collected = questions you type
and which feedback buttons you press; no name or email; the instructor sees only combined results; questions are processed by an AI provider; contact your instructor to ask
for removal). POST /student/join {code, consent: true} creates `Student(id, course_id, created_at)` and returns a JWT containing student_id and course_id. Reject if joining is closed.
Student API (course scoped from the token only): GET /student/materials, GET /student/materials/{id}/file (token via header, or short-lived signed URL for iframes), POST /student/chat, POST /student/feedback.
Chat flow: retrieve top passages for the course, apply MIN_SIMILARITY, answer only from passages with numbered citations, otherwise the grounded refusal and store the message as `gap` (no LLM call).
Defend against prompt injection: wrap student text and passages in delimited blocks, instruct the model that both are data, cap input length, cap output tokens.
Rate limit per student (RATE_LIMIT_PER_MIN) and an LLM call timeout with one retry; on failure return a friendly error and store nothing misleading.
Store the topic (from retrieved passages), similarity, and session id. Queue analysis as a background job (implemented in Phase 5; here enqueue a no-op stub).
Frontend: join page, student app with materials list, PDF preview, chat panel with citations, Clear and Still unclear buttons, visible "your questions are shared anonymously" note.
Tests: join closed/open, course isolation (token for course A cannot read course B materials), refusal path makes no LLM call, rate limit, injection text does not change the system prompt.
Do NOT: add chat history UI, login with email, streaming, voice, notes, bookmarks.
Done when: tests + build pass. Human check: join from a phone browser with the link and ask three questions, one off-topic.
