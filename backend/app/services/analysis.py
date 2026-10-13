"""Per-message intent analysis. Runs in the background so students never wait for it."""
import asyncio
import json
import re
from sqlmodel import Session
from ..config import settings
from ..db import engine
from ..models import Message
from . import llm, rag

RUBRIC = """You label ONE student message sent to a course tutor.
confusion = the student expresses misunderstanding, states a belief that conflicts with the course passage, says they do not get it, or asks again because an earlier answer did not help.
information = a request for facts, how-to, recommendations or extra detail with no sign of misunderstanding.
other = anything else.
Return JSON only: {"intent":"confusion|information|other","misconception":true|false,"confidence":0.0-1.0,"evidence_phrase":"exact words from the student message that show it, or empty"}"""
_model = None


async def judge(text: str, passage: str) -> dict:
    raw = await llm.chat([{"role": "system", "content": RUBRIC},
                          {"role": "user", "content": f"Course passage:\n{passage}\n\nStudent message:\n{text}"}], json_mode=True, temperature=0)
    m = re.search(r"\{.*\}", raw, re.S)
    return json.loads(m.group(0)) if m else {}


def logreg(text: str) -> dict:
    global _model
    import joblib, numpy as np
    if _model is None:
        _model = joblib.load(settings.intent_model_path)
    p = _model["clf"].predict_proba(rag.ef()([text]))[0]
    i = int(np.argmax(p))
    intent = _model["clf"].classes_[i]
    if intent == "confusion" and p[i] < _model["threshold"]:
        intent = "other"
    return {"intent": intent, "misconception": False, "confidence": float(p[i]), "evidence_phrase": ""}


async def analyze(message_id: int) -> None:
    with Session(engine) as s:
        m = s.get(Message, message_id)
        if not m or m.intent:
            return
        hits = await asyncio.to_thread(rag.retrieve, m.text, 1)
        try:
            r = await judge(m.text, hits[0]["text"] if hits else "") if settings.intent_backend == "llm" else await asyncio.to_thread(logreg, m.text)
        except Exception:
            return  # left unlabelled; a batch job can retry later
        phrase = r.get("evidence_phrase") or ""
        m.intent = r.get("intent") if r.get("intent") in ("confusion", "information", "other") else "other"
        m.intent_conf = float(r.get("confidence") or 0)
        m.misconception = bool(r.get("misconception"))
        m.phrase = phrase if phrase and phrase in m.text else ""
        s.add(m)
        s.commit()
