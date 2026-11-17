"""Topic attribution: which course topic a student question counts towards."""
from types import SimpleNamespace

import numpy as np

from app.services import ingest, rag


def hit(sim, keys="", key=""):
    return {"sim": sim, "text": "", "meta": {"topic_keys": keys, "topic_key": key or keys.split(",")[0]}}


def test_best_passage_wins_over_several_weak_ones():
    # The real failure from the e2e run: the right passage (0.40) lost to two weak slides (0.28 + 0.27).
    hits = [hit(0.40, "gradient-descent"), hit(0.34, "bias-variance"),
            hit(0.28, "evaluation-metrics"), hit(0.27, "evaluation-metrics")]
    assert rag.topic_of(hits) == "gradient-descent"


def test_near_tie_is_settled_by_the_question():
    # One summary passage covers every topic, so all of them score the same.
    hits = [hit(0.49, "bias-variance,gradient-descent,evaluation-metrics")]
    asked = []

    def tie_break(keys):
        asked.append(sorted(keys))
        return "gradient-descent"

    assert rag.topic_of(hits, tie_break) == "gradient-descent"
    assert asked == [["bias-variance", "evaluation-metrics", "gradient-descent"]]


def test_clear_winner_does_not_need_a_tie_break():
    def tie_break(keys):
        raise AssertionError("not needed")

    assert rag.topic_of([hit(0.60, "clustering"), hit(0.40, "bias-variance")], tie_break) == "clustering"


def test_chunks_indexed_before_multi_topic_tags_still_work():
    hits = [{"sim": 0.5, "text": "", "meta": {"topic_key": "clustering"}}]
    assert rag.topic_of(hits) == "clustering"


def test_refused_or_untagged_hits_have_no_topic():
    assert rag.topic_of([hit(0.10, "clustering")]) is None
    assert rag.topic_of([{"sim": 0.6, "text": "", "meta": {}}]) is None


WORDS = ["learning", "variance", "precision"]


def fake_ef(texts):
    """Bag-of-keywords 'embedding' so the test is deterministic and needs no model."""
    return [[1.0 if word in text.lower() else 0.0 for word in WORDS] + [0.01] for text in texts]


def test_summary_chunk_is_tagged_with_every_topic_it_covers(monkeypatch):
    monkeypatch.setattr(rag, "ef", lambda: fake_ef)
    concepts = [SimpleNamespace(key="gd", name="Gradient descent", description="The learning rate."),
                SimpleNamespace(key="bv", name="Bias-variance", description="High variance overfits."),
                SimpleNamespace(key="em", name="Metrics", description="Precision and recall.")]
    summary = ("The learning rate controls the step size of each update.\n"
               "High variance models overfit the training data badly.\n"
               "Precision is the share of predicted positives that are right.")
    single = "A large learning rate makes the loss diverge or oscillate."
    docs = [summary, single]
    tags = ingest.tag_chunks(docs, np.array(fake_ef(docs), dtype=float), concepts)
    assert sorted(tags[0]) == ["bv", "em", "gd"]
    assert tags[1] == ["gd"]
