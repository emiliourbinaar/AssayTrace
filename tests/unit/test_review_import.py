"""Synthetic review decisions; none represents an actual human confirmation."""
import pytest

from assaytrace.review import ReviewContractError, import_reviews, review_queue


def test_review_import_preserves_unvisited_assays_and_separates_audit_metadata():
    queue = review_queue([
        {"assay_id": 1, "molecule_count": 10},
        {"assay_id": 2, "molecule_count": 5},
    ], "synthetic", limit_each=1)
    decision = {"source_id": "synthetic", "assay_id": 1, "category": "compatible",
                "confirmation_state": "assistant_proposed", "evidence_refs": ["synthetic:e1"],
                "record_exceptions": [], "reviewer": "synthetic-author", "reviewed_at": "synthetic-time"}
    result = import_reviews(queue, [decision])
    assert result is not None
    assert result["unreviewed"] == [2]
    assert result["selection_sha256"] == queue["selection_sha256"]
    assert result["decisions"] == [{key: value for key, value in decision.items()
                                    if key not in {"reviewer", "reviewed_at"}}]
    assert result["audit"] == [{"assay_id": 1, "reviewer": "synthetic-author", "reviewed_at": "synthetic-time"}]
    revised_time = import_reviews(queue, [{**decision, "reviewed_at": "another-time"}])
    assert revised_time["semantic_sha256"] == result["semantic_sha256"]
    assert revised_time["audit"] != result["audit"]


@pytest.mark.parametrize("changes", [
    {"source_id": "wrong-release"}, {"assay_id": 99},
    {"confirmation_state": "automatically_confirmed"},
    {"category": "probably_ok"}, {"evidence_refs": []},
    {"evidence_refs": "not-a-list"}, {"record_exceptions": "not-a-list"},
])
def test_import_rejects_unlinked_or_unsupported_decisions(changes):
    queue = review_queue([{"assay_id": 1, "molecule_count": 10}], "synthetic")
    decision = {"source_id": "synthetic", "assay_id": 1, "category": "compatible",
                "confirmation_state": "assistant_proposed", "evidence_refs": ["synthetic:e1"],
                "record_exceptions": []}
    with pytest.raises(ReviewContractError):
        import_reviews(queue, [{**decision, **changes}])


def test_review_rationale_and_missing_evidence_are_preserved_in_scientific_identity():
    queue = review_queue([{"assay_id": 1, "molecule_count": 10}], "synthetic")
    decision = {"source_id": "synthetic", "assay_id": 1, "doc_id": 7, "category": "unresolved",
                "confirmation_state": "assistant_proposed", "evidence_refs": ["synthetic:e1"],
                "record_exceptions": [], "rationale": "Enzyme origin unspecified",
                "missing_evidence": ["Human enzyme source and cell-free preparation"]}
    first = import_reviews(queue, [decision])
    assert first["decisions"][0].get("rationale") == decision["rationale"]
    assert first["decisions"][0].get("missing_evidence") == decision["missing_evidence"]
    assert first["decisions"][0].get("doc_id") == 7
    second = import_reviews(queue, [{**decision, "rationale": "Conflicting enzyme origin evidence"}])
    assert second["semantic_sha256"] != first["semantic_sha256"]


def test_duplicate_assay_decisions_cannot_silently_overwrite_one_another():
    queue = review_queue([{"assay_id": 1, "molecule_count": 10}], "synthetic")
    decision = {"source_id": "synthetic", "assay_id": 1, "category": "compatible",
                "confirmation_state": "assistant_proposed", "evidence_refs": ["synthetic:e1"],
                "record_exceptions": []}
    with pytest.raises(ReviewContractError, match="Duplicate"):
        import_reviews(queue, [decision, {**decision, "category": "incompatible"}])


def test_changed_frozen_queue_is_rejected_before_review_import():
    queue = review_queue([{"assay_id": 1, "molecule_count": 10}], "synthetic")
    queue["order"].append(999)
    with pytest.raises(ReviewContractError, match="selection digest"):
        import_reviews(queue, [])


@pytest.mark.parametrize("changes", [
    {"reason": "automatic_scientific_failure"}, {"evidence_refs": []},
    {"explanation": ""}, {"confirmation_state": "automatically_confirmed"},
])
def test_decisive_blocker_requires_explicit_supported_evidence_fields(changes):
    queue = review_queue([{"assay_id": 1, "molecule_count": 10}], "synthetic")
    stop = {"reason": "decisive_blocker", "evidence_refs": ["synthetic:e1"],
            "explanation": "Synthetic blocker", "confirmation_state": "assistant_proposed"}
    with pytest.raises(ReviewContractError):
        import_reviews(queue, [], stop={**stop, **changes})


@pytest.mark.parametrize("changes", [
    {"evidence_refs": [""]}, {"evidence_refs": [None]},
    {"record_exceptions": [{}]},
    {"record_exceptions": [{"activity_id": 1, "reason": "mutant", "evidence_refs": []}]},
    {"record_exceptions": [{"activity_id": 1, "reason": "", "evidence_refs": ["synthetic:e1"]}]},
])
def test_review_evidence_and_record_exceptions_require_traceable_nonempty_fields(changes):
    queue = review_queue([{"assay_id": 1, "molecule_count": 10}], "synthetic")
    decision = {"source_id": "synthetic", "assay_id": 1, "category": "compatible",
                "confirmation_state": "assistant_proposed", "evidence_refs": ["synthetic:e1"],
                "record_exceptions": []}
    with pytest.raises(ReviewContractError):
        import_reviews(queue, [{**decision, **changes}])
