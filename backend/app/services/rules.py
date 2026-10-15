"""Pure insight decision rules."""
from dataclasses import dataclass
import math


@dataclass
class Stats:
    students_asked: int = 0
    students_confused: int = 0
    persist_students: int = 0
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
    quiz_flag = st.quiz_rate is not None and st.quiz_rate < quiz_low
    persistence_flag = st.persist_students >= 3
    if st.students_confused >= min_students and (quiz_flag or persistence_flag):
        confidence = "High" if st.students_confused >= 6 and quiz_flag else "Medium"
        tier = "needs_attention"
    elif st.students_confused >= 2:
        confidence, tier = None, "watch"
    else:
        confidence, tier = None, "none"
    return {
        "tier": tier,
        "confidence": confidence,
        "quiz_flag": quiz_flag,
        "persistence_flag": persistence_flag,
        "corroborated": quiz_flag or persistence_flag,
        "share": round(st.students_confused / max(enrolled, 1), 3),
        "share_lower": round(wilson_lower(st.students_confused, enrolled), 3),
    }
