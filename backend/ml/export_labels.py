"""python -m ml.export_labels data/to_label.csv -> sheet to hand-label (confusion | information | other)."""
import csv, sys
from collections import defaultdict
from sqlmodel import Session, select
from app.db import engine
from app.models import Message

with Session(engine) as s:
    turn, rows = defaultdict(int), []
    for m in s.exec(select(Message).order_by(Message.session_id, Message.created_at)).all():
        turn[m.session_id] += 1
        rows.append({"id": m.id, "text": m.text, "label": "", "turn": turn[m.session_id]})
w = csv.DictWriter(open(sys.argv[1], "w", newline="", encoding="utf-8"), fieldnames=["id", "text", "label", "turn"])
w.writeheader(); w.writerows(rows)
print(f"Wrote {len(rows)} rows. Fill the label column, have a second person label too, then run ml.evaluate.")
