"""Authored criterion decisions; these do not assess actual ChEMBL feasibility."""
import pytest

from assaytrace.profile import conclusions


@pytest.mark.parametrize("statuses,expected", [
    (["supported", "supported", "inconclusive"], {"prediction": "supported", "study": "inconclusive"}),
    (["supported", "supported", "not_supported"], {"prediction": "supported", "study": "not_supported"}),
    (["supported", "supported", "supported"], {"prediction": "supported", "study": "supported"}),
    (["inconclusive", "supported", "supported"], {"prediction": "inconclusive", "study": "inconclusive"}),
    (["not_supported", "inconclusive", "supported"], {"prediction": "not_supported", "study": "not_supported"}),
])
def test_prediction_and_study_conclusions_use_their_distinct_required_criteria(statuses, expected):
    criteria = {name: {"status": status, "evidence_refs": ["synthetic:e1"],
                       "limitations": ["Synthetic only"], "scope": "Synthetic population",
                       "reviewer_confirmation": "human_confirmed", "next_action": "Review next phase"}
                for name, status in zip(("population", "allocation", "curation"), statuses)}
    assert conclusions(criteria) == expected


@pytest.mark.parametrize("changes", [
    {"status": "probably_supported"}, {"evidence_refs": []}, {"evidence_refs": "source"},
    {"limitations": None}, {"scope": ""}, {"next_action": ""},
    {"reviewer_confirmation": "assistant_proposed"},
])
def test_conclusions_reject_incomplete_or_unconfirmed_supported_criteria(changes):
    criterion = {"status": "supported", "evidence_refs": ["synthetic:e1"],
                 "limitations": ["Synthetic only"], "scope": "Synthetic population",
                 "reviewer_confirmation": "human_confirmed", "next_action": "Review next phase"}
    criteria = {name: dict(criterion) for name in ("population", "allocation", "curation")}
    criteria["curation"].update(changes)
    with pytest.raises(ValueError):
        conclusions(criteria)


@pytest.mark.parametrize("confirmation", [None, "automatic"])
def test_inconclusive_criteria_still_require_an_explicit_recognized_review_state(confirmation):
    criteria = {name: {"status": "inconclusive", "evidence_refs": ["synthetic:budget-stop"],
                       "limitations": ["Review incomplete"], "scope": "Synthetic",
                       "reviewer_confirmation": confirmation, "next_action": "Complete review"}
                for name in ("population", "allocation", "curation")}
    with pytest.raises(ValueError):
        conclusions(criteria)
