"""Turns labelled messages into topic-level insights. The decision rules are pure functions (see tests)."""
import math
from collections import defaultdict
from dataclasses import dataclass
from sqlmodel import Session, select
from ..config import settings
from ..models import Concept, Message, QuizItem, QuizResponse, Verdict


@dataclass
class Stats:
    students_asked: int = 0
    students_confused: int = 0
    persist_students: int = 0   # students with 2+ confusion messages on the topic
    messages: int = 0
    confusion_msgs: int = 0
    info_msgs: int = 0
    quiz_rate: float | None = None


def wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = k / n
    return (p + z * z / (2 * n) - z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)) / (1 + z * z / n)


def classify(st: Stats, enrolled: int, min_students: int, quiz_low: float) -> dict:
    """Needs attention only if enough DISTINCT students show confusion AND an independent signal agrees."""
    quiz_flag = st.quiz_rate is not None and st.quiz_rate < quiz_low
    corroborated = quiz_flag or st.persist_students >= 3
    if st.students_confused >= min_students and corroborated:
        tier, conf = "needs_attention", ("High" if st.students_confused >= 6 and quiz_flag else "Medium")
    elif st.students_confused >= 2:
        tier, conf = "watch", None
    else:
        tier, conf = "none", None
    return {"tier": tier, "confidence": conf, "quiz_flag": quiz_flag, "corroborated": corroborated,
            "share": round(st.students_confused / max(enrolled, 1), 3),
            "share_lower": round(wilson_lower(st.students_confused, enrolled), 3)}


def build_stats(s: Session, c: Concept, since=None) -> tuple[Stats, list[Message]]:
    q = select(Message).where(Message.concept_id == c.id)
    msgs = [m for m in s.exec(q).all() if since is None or m.created_at > since]
    conf = [m for m in msgs if m.intent == "confusion" and m.intent_conf >= settings.min_conf]
    per = defaultdict(int)
    for m in conf:
        per[m.student_id] += 1
    ids = [i.id for i in s.exec(select(QuizItem).where(QuizItem.concept_id == c.id)).all()]
    resp = [r for r in s.exec(select(QuizResponse)).all() if r.item_id in ids]
    st = Stats(len({m.student_id for m in msgs}), len(per), sum(1 for v in per.values() if v >= 2), len(msgs), len(conf),
               sum(1 for m in msgs if m.intent == "information"), (sum(r.correct for r in resp) / len(resp)) if resp else None)
    return st, conf


def _verdict(s: Session, c: Concept):
    return s.exec(select(Verdict).where(Verdict.concept_id == c.id).order_by(Verdict.created_at.desc())).first()


def topics(s: Session) -> dict:
    flagged, quiet = [], []
    for c in s.exec(select(Concept)).all():
        v = _verdict(s, c)
        st, _ = build_stats(s, c, v.created_at if v and v.verdict == "false_alarm" else None)
        r = classify(st, settings.enrolled, settings.min_students, settings.quiz_low)
        if r["tier"] == "needs_attention":
            flagged.append({"id": c.id, "name": c.name, "module": c.module, "share": r["share"], "confidence": r["confidence"],
                            "status": v.verdict if v and v.verdict == "addressed" else "review"})
        elif st.messages >= 8:
            quiet.append({"name": c.name, "reason": "Many questions, but mostly requests for information." if st.info_msgs >= st.confusion_msgs else "Not enough students show confusion yet."})
    msgs = s.exec(select(Message)).all()
    return {"summary": {"questions": len(msgs), "students_asking": len({m.student_id for m in msgs}), "enrolled": settings.enrolled,
                        "needs_attention": sum(1 for f in flagged if f["status"] == "review")},
            "flagged": sorted(flagged, key=lambda f: -f["share"]), "not_flagged": quiet}


def groups(msgs: list[Message]) -> list[dict]:
    """Cluster confusion messages by meaning (agglomerative, cosine); title = most central message."""
    if not msgs:
        return []
    labels = [0] * len(msgs)
    if len(msgs) >= 3:
        import numpy as np
        from sklearn.cluster import AgglomerativeClustering
        from . import rag
        X = np.array(rag.ef()([m.text for m in msgs]), dtype=float)
        labels = AgglomerativeClustering(n_clusters=None, distance_threshold=0.8, metric="cosine", linkage="average").fit_predict(X).tolist()
    out = defaultdict(list)
    for m, l in zip(msgs, labels):
        out[l].append(m)
    res = []
    for items in sorted(out.values(), key=len, reverse=True):
        res.append({"title": (items[0].text[:80]), "count": len(items),
                    "items": [{"id": m.id, "text": m.text, "phrase": m.phrase, "misconception": m.misconception} for m in items]})
    return res


def detail(s: Session, cid: int) -> dict | None:
    c = s.get(Concept, cid)
    if not c:
        return None
    v = _verdict(s, c)
    st, conf = build_stats(s, c, v.created_at if v and v.verdict == "false_alarm" else None)
    r = classify(st, settings.enrolled, settings.min_students, settings.quiz_low)
    info = [m.text for m in s.exec(select(Message).where(Message.concept_id == c.id, Message.intent == "information")).all()]
    quiz = (f"{round(st.quiz_rate*100)}% answered the related quiz question correctly." if st.quiz_rate is not None else "No quiz item for this topic yet.")
    return {"id": c.id, "name": c.name, "module": c.module, "confidence": r["confidence"], "tier": r["tier"], "status": v.verdict if v else None,
            "stats": st.__dict__, "share": r["share"], "share_lower": r["share_lower"],
            "checks": [{"ok": st.students_confused >= settings.min_students, "text": f"{st.students_confused} of {st.students_asked} students who asked showed confusion (minimum is {settings.min_students})."},
                       {"ok": st.confusion_msgs > 0, "text": f"{st.confusion_msgs} of {st.messages} questions showed confusion. {st.info_msgs} only asked for information and were not counted."},
                       {"ok": r["corroborated"], "text": quiz if st.quiz_rate is not None else f"{st.persist_students} students asked about it more than once. {quiz}"}],
            "groups": groups(conf), "excluded": info[:10]}
