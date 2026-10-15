from app.services.insights import Stats, classify, wilson_lower
from app.services.ingest import chunk

C = dict(enrolled=24, min_students=4, quiz_low=0.6)


def test_rule_boundaries_are_table_driven():
    cases = [
        (3, 3, 0, None, "watch"),
        (4, 4, 0, 0.60, "watch"),
        (4, 4, 0, 0.599, "needs_attention"),
        (4, 4, 0, None, "watch"),
        (6, 6, 0, 0.599, "needs_attention"),
    ]
    for students, confused, persistent, quiz_rate, tier in cases:
        assert classify(Stats(students, confused, persistent, 10, confused, 0, quiz_rate), **C)["tier"] == tier


def test_information_gap_and_repeated_messages_rules():
    assert classify(Stats(10, 4, 0, 10, 0, 10, None), **C)["tier"] == "watch"
    assert classify(Stats(10, 0, 3, 10, 0, 0, None), **C)["tier"] == "none"
    assert classify(Stats(10, 4, 3, 10, 4, 0, None), **C)["tier"] == "needs_attention"


def test_six_students_and_quiz_are_high_but_persistence_is_medium():
    assert classify(Stats(8, 6, 0, 8, 6, 0, 0.59), **C)["confidence"] == "High"
    assert classify(Stats(8, 4, 3, 8, 4, 0, None), **C)["confidence"] == "Medium"


def test_share_and_small_counts():
    result = classify(Stats(10, 4, 0, 10, 4, 0, None), enrolled=20, min_students=4, quiz_low=0.6)
    assert result["share"] == 0.2


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


def test_ten_messages_from_one_student_count_once():
    result = classify(Stats(1, 1, 10, 10, 10, 0, 0.1), **C)
    assert result["tier"] == "none"


def test_chunking_respects_size():
    text = "\n\n".join(["word " * 100] * 10)
    assert all(len(c) <= 1400 for c in chunk(text))
