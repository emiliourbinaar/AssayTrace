"""Authored eligibility cases, not actual human-confirmed assay decisions."""
import pytest

from assaytrace.review import metadata_reasons, reviewed_record_reasons, record_eligibility


@pytest.mark.parametrize("field,value,expected", [
    (None, None, []),
    ("assay_type", "F", ["assay_type_mismatch"]),
    ("confidence_score", 8, ["confidence_score_mismatch"]),
    ("relationship_type", "H", ["relationship_type_mismatch"]),
    ("assay_organism", None, ["assay_organism_missing"]),
    ("assay_organism", "Electrophorus electricus", ["assay_organism_mismatch"]),
    ("tid", 999, ["target_link_mismatch"]),
])
def test_assay_metadata_is_screened_locally_without_inference_from_human_target(field, value, expected):
    target = {"tid": 93, "chembl_id": "CHEMBL220", "target_type": "SINGLE PROTEIN",
              "organism": "Homo sapiens"}
    assay = {"tid": 93, "assay_type": "B", "confidence_score": 9,
             "relationship_type": "D", "assay_organism": "Homo sapiens"}
    if field is not None:
        assay[field] = value
    assert metadata_reasons(assay, target) == expected


@pytest.mark.parametrize("field,value,reason", [
    ("chembl_id", "CHEMBL_OTHER", "target_identity_mismatch"),
    ("target_type", "PROTEIN FAMILY", "target_type_mismatch"),
    ("organism", None, "target_organism_missing"),
    ("organism", "Mus musculus", "target_organism_mismatch"),
    ("tid", None, "target_link_missing"),
])
def test_target_identity_and_missing_links_are_not_assumed(field, value, reason):
    target = {"tid": 93, "chembl_id": "CHEMBL220", "target_type": "SINGLE PROTEIN",
              "organism": "Homo sapiens"}
    assay = {"tid": 93, "assay_type": "B", "confidence_score": 9,
             "relationship_type": "D", "assay_organism": "Homo sapiens"}
    target[field] = value
    if field == "tid":
        assay["tid"] = None
    assert metadata_reasons(assay, target) == [reason]


@pytest.mark.parametrize("section,field,value,expected", [
    (None, None, None, []),
    ("review", "confirmation_state", "assistant_proposed", ["review_not_human_confirmed"]),
    ("review", "category", "unresolved", ["assay_not_compatible"]),
    ("review", "evidence_refs", [], ["review_evidence_missing"]),
    ("review", "assay_id", 2, ["review_assay_link_mismatch"]),
    ("review", "source_id", "another-release", ["review_source_mismatch"]),
    ("activity", "standard_relation", ">", ["numerical:non_exact_relation"]),
    ("activity", "standard_type", "Ki", ["wrong_endpoint"]),
    ("activity", "data_validity_comment", "Potential missing data", ["validity_flag_not_permitted"]),
    ("activity", "potential_duplicate", 1, []),
    ("chemistry", "identity_id", None, ["structure_unresolved"]),
    ("chemistry", "structure_equivalence_key", None, ["equivalence_unresolved"]),
])
def test_record_eligibility_intersects_confirmed_review_with_scientific_contracts(section, field, value, expected):
    inputs = {
        "activity": {"source_id": "synthetic", "assay_id": 1, "standard_type": "IC50",
                     "standard_value": "10", "standard_units": "nM", "standard_relation": "=",
                     "data_validity_comment": None, "potential_duplicate": 0},
        "review": {"source_id": "synthetic", "assay_id": 1, "category": "compatible",
                   "confirmation_state": "human_confirmed", "evidence_refs": ["synthetic:review-1"]},
        "chemistry": {"identity_id": "i1", "structure_equivalence_key": "e1"},
    }
    if section is not None:
        inputs[section][field] = value
    assert reviewed_record_reasons(**inputs, metadata_issues=[], group_issues=[], record_conflicts=[]) == expected


def test_assay_acceptance_cannot_override_record_issues_or_allocation_quarantine():
    activity = {"source_id": "synthetic", "assay_id": 1, "standard_type": "IC50",
                "standard_value": "10", "standard_units": "nM", "standard_relation": "="}
    review = {"source_id": "synthetic", "assay_id": 1, "category": "compatible",
              "confirmation_state": "human_confirmed", "evidence_refs": ["synthetic:review-1"]}
    chemistry = {"identity_id": "i1", "structure_equivalence_key": "e1"}
    assert reviewed_record_reasons(
        activity, review, chemistry,
        metadata_issues=["confidence_score_mismatch"],
        group_issues=["parent_equivalence_conflict"],
        record_conflicts=["mutant_target"],
    ) == ["metadata:confidence_score_mismatch",
          "allocation_quarantine:parent_equivalence_conflict", "record_conflict:mutant_target"]
    assert activity["standard_value"] == "10"
    assert chemistry["identity_id"] == "i1"


@pytest.mark.parametrize("field,reason", [
    ("source_id", "review_source_missing"),
    ("assay_id", "review_assay_link_missing"),
])
def test_two_missing_review_links_do_not_establish_a_match(field, reason):
    activity = {"source_id": "synthetic", "assay_id": 1, "standard_type": "IC50",
                "standard_value": "10", "standard_units": "nM", "standard_relation": "="}
    review = {"source_id": "synthetic", "assay_id": 1, "category": "compatible",
              "confirmation_state": "human_confirmed", "evidence_refs": ["synthetic:review-1"]}
    activity.pop(field)
    review.pop(field)
    assert reviewed_record_reasons(
        activity, review, {"identity_id": "i1", "structure_equivalence_key": "e1"},
        metadata_issues=[], group_issues=[], record_conflicts=[],
    ) == [reason]


def test_group_quarantine_blocks_allocation_without_invalidating_measurement():
    activity = {"source_id": "synthetic", "assay_id": 1, "standard_type": "IC50",
                "standard_value": "10", "standard_units": "nM", "standard_relation": "="}
    review = {"source_id": "synthetic", "assay_id": 1, "category": "compatible",
              "confirmation_state": "human_confirmed", "evidence_refs": ["synthetic:review-1"]}
    result = record_eligibility(
        activity, review, {"identity_id": "i1", "structure_equivalence_key": "e1"},
        metadata_issues=[], group_issues=["parent_equivalence_conflict"], record_conflicts=[],
    )
    assert result == {"measurement_eligible": True, "allocation_eligible": False,
                      "measurement_reasons": [],
                      "allocation_reasons": ["allocation_quarantine:parent_equivalence_conflict"]}


@pytest.mark.parametrize("activity_id,expected", [(1, ["record_conflict:mutant_target"]), (2, [])])
def test_imported_record_exception_applies_only_to_its_source_activity(activity_id, expected):
    activity = {"source_id": "synthetic", "assay_id": 1, "activity_id": activity_id,
                "standard_type": "IC50", "standard_value": "10", "standard_units": "nM", "standard_relation": "="}
    review = {"source_id": "synthetic", "assay_id": 1, "category": "compatible",
              "confirmation_state": "human_confirmed", "evidence_refs": ["synthetic:e1"],
              "record_exceptions": [{"activity_id": 1, "reason": "mutant_target", "evidence_refs": ["synthetic:e2"]}]}
    result = reviewed_record_reasons(activity, review, {"identity_id": "i1", "structure_equivalence_key": "e1"},
                                     metadata_issues=[], group_issues=[], record_conflicts=[])
    assert result == expected
