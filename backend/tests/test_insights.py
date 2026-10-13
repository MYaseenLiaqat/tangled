from app.services.insights import Stats, classify, wilson_lower
from app.services.ingest import chunk

C = dict(enrolled=24, min_students=4, quiz_low=0.6)


def test_wilson_grows_with_evidence():
    assert wilson_lower(0, 0) == 0
    assert 0 < wilson_lower(8, 24) < 8 / 24


def test_strong_topic_is_flagged_high():
    r = classify(Stats(11, 8, 6, 38, 21, 14, 0.45), **C)
    assert r["tier"] == "needs_attention" and r["confidence"] == "High"


def test_many_questions_but_little_confusion_is_not_flagged():
    r = classify(Stats(12, 3, 0, 29, 5, 22, 0.86), **C)
    assert r["tier"] != "needs_attention"


def test_confusion_without_corroboration_is_only_watch():
    r = classify(Stats(10, 5, 1, 20, 9, 10, 0.80), **C)
    assert r["tier"] == "watch"


def test_persistence_can_corroborate_without_quiz():
    r = classify(Stats(10, 5, 3, 20, 9, 10, None), **C)
    assert r["tier"] == "needs_attention" and r["confidence"] == "Medium"


def test_too_few_students_never_flags():
    assert classify(Stats(3, 3, 3, 9, 9, 0, 0.1), **C)["tier"] == "watch"


def test_chunking_respects_size():
    text = "\n\n".join(["word " * 100] * 10)
    assert all(len(c) <= 1400 for c in chunk(text))
