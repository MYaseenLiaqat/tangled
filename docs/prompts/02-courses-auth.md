# Phase 2: Instructor accounts, courses, join codes (F1, F2)
Read `.github/copilot-instructions.md` and `docs/SCOPE.md`. Build ONLY F1 and F2.

Data: `Instructor(id, email unique, password_hash, created_at)`, `Course(id, instructor_id, name, class_size nullable, join_code unique, joining_open bool, created_at)`.
Add `course_id` (indexed, FK) to Concept, Material, Message, QuizItem, Verdict and any other course-owned table; add an Alembic migration.
Remove the shared TEACHER_TOKEN and the seeded student codes.

API (`/api/v1`): POST /auth/register, POST /auth/login (argon2, JWT 12h), GET /me, POST/GET /courses, GET/PATCH /courses/{id}
(name, class_size, joining_open), POST /courses/{id}/join-code/regenerate.
Create a shared dependency `get_owned_course(course_id)` that every instructor route uses; it returns 404 if the course is not the caller's.
Join codes: 6 characters from an unambiguous alphabet (no 0/O/1/I), generated with `secrets`, unique.
Frontend: login/register page, course list, create-course form, course page showing the join code and link `/join/{code}` with copy buttons and an open/closed toggle. Existing pages move under `/courses/:id/...`.
Tests: register/login; course isolation (instructor B cannot read A's course, 404); regenerate code invalidates the old code; closed joining flag stored.
Do NOT: add student join, email, password reset, roles, organisations, OAuth.
Done when: tests + build pass. Human check: register, create a course, copy the join link.
