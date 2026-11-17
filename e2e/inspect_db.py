"""Print what the backend has stored, to check results behind the UI.

Usage (repo root):
    backend/.venv/Scripts/python e2e/inspect_db.py                       # default e2e database
    backend/.venv/Scripts/python e2e/inspect_db.py backend/data/tangled.db
"""
import sqlite3
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "backend/data/e2e/tangled.db"
db = sqlite3.connect(path)


def show(title: str, sql: str) -> None:
    print(f"\n== {title}")
    rows = db.execute(sql).fetchall()
    for row in rows:
        print("  ", row)
    if not rows:
        print("   (none)")


show("Counts", "select (select count(*) from instructor) instructors, (select count(*) from course) courses, "
     "(select count(*) from concept) topics, (select count(*) from material) materials, "
     "(select count(*) from student) students, (select count(*) from message) messages")
show("Courses (id, name, code, open, class size)", "select id, name, join_code, joining_open, class_size from course")
show("Materials (id, course, file, status, chunks, error)",
     "select id, course_id, filename, status, chunks, error from material")
show("Messages (id, student, topic, intent, conf, evidence)",
     "select id, student_id, concept_id, intent, round(intent_conf, 2), substr(phrase, 1, 50) from message")
show("Analysis jobs (message, status, attempts, error)",
     "select message_id, status, attempts, last_error from analysisjob")
show("Failed / pending analysis", "select message_id, status, last_error from analysisjob where status != 'done'")
show("Instructor verdicts", "select course_id, concept_id, verdict, created_at from verdict")
show("Students: is any personal data stored? (should be ids only)", "select * from student limit 5")
