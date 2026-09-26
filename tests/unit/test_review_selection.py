"""Authored assay metadata, not captured ChEMBL records."""
from assaytrace.review import review_queue
import pytest


def test_high_coverage_selection_uses_compound_count_then_assay_id():
    rows = [
        {"assay_id": 3, "molecule_count": 5, "bao_format": "F1", "document_year": 2015},
        {"assay_id": 2, "molecule_count": 10, "bao_format": "F1", "document_year": 2015},
        {"assay_id": 1, "molecule_count": 5, "bao_format": "F2", "document_year": 2005},
    ]
    queue = review_queue(rows, "synthetic", limit_each=2)
    assert queue is not None
    assert queue["high"] == [2, 1]
    assert queue == review_queue(list(reversed(rows)), "synthetic", limit_each=2)


def test_frozen_coverage_and_stratified_streams_are_disjoint_and_interleaved():
    rows = [
        {"assay_id": 1, "molecule_count": 100, "bao_format": "F1", "document_year": 2015},
        {"assay_id": 2, "molecule_count": 90, "bao_format": "F1", "document_year": 2015},
        {"assay_id": 3, "molecule_count": 2, "bao_format": "F2", "document_year": 2005},
        {"assay_id": 4, "molecule_count": 1, "bao_format": "F1", "document_year": 2015},
    ]
    queue = review_queue(rows, "synthetic", limit_each=2)
    assert queue.get("stratified") == [4, 3]
    assert queue["high"] == [1, 2]
    assert queue["order"] == [1, 4, 2, 3]
    assert queue == review_queue(list(reversed(rows)), "synthetic", limit_each=2)


@pytest.mark.parametrize("year,band", [(1999, "BEFORE_2000"), (2000, "2000_2009"),
    (2009, "2000_2009"), (2010, "2010_2019"), (2019, "2010_2019"),
    (2020, "2020_PLUS"), (None, "UNKNOWN"), ("unparseable", "UNKNOWN")])
def test_frozen_strata_include_unknowns_and_declared_year_boundaries(year, band):
    rows = [{"assay_id": 1, "molecule_count": 2, "bao_format": None, "document_year": year}]
    queue = review_queue(rows, "synthetic", limit_each=2)
    assert queue.get("strata") == [{"assay_id": 1, "bao_format": "UNKNOWN", "year_band": band}]
    assert queue["order"] == [1]


def test_selection_identity_tracks_sampling_metadata_and_source_but_not_review_or_potency():
    row = {"assay_id": 1, "molecule_count": 2, "bao_format": "F1", "document_year": 2005}
    queue = review_queue([row], "synthetic", limit_each=2)
    assert len(queue.get("metadata_sha256", "")) == 64
    assert len(queue.get("selection_sha256", "")) == 64
    assert queue == review_queue([{**row, "pic50": "9", "manual_decision": "compatible"}],
                                "synthetic", limit_each=2)
    changed_year = review_queue([{**row, "document_year": 2006}], "synthetic", limit_each=2)
    assert changed_year["metadata_sha256"] != queue["metadata_sha256"]
    assert changed_year["selection_sha256"] != queue["selection_sha256"]
    changed_source = review_queue([row], "another-synthetic-release", limit_each=2)
    assert changed_source["selection_sha256"] != queue["selection_sha256"]


@pytest.mark.parametrize("limit", [-1, 0, 61, True])
def test_review_stream_limit_cannot_exceed_the_approved_cap(limit):
    with pytest.raises(ValueError, match="1.*60"):
        review_queue([], "synthetic", limit_each=limit)


def test_stratified_round_robin_uses_fixed_hash_order_within_each_stratum():
    rows = [
        {"assay_id": assay, "molecule_count": count, "bao_format": format_id, "document_year": 2015}
        for assay, count, format_id in [
            (1, 100, "A"), (2, 90, "A"), (3, 80, "A"), (10, 70, "A"),
            (4, 1, "A"), (5, 1, "A"), (6, 1, "A"),
            (7, 1, "B"), (8, 1, "B"), (9, 1, "C"),
        ]
    ]
    # Independently checked SHA-256 ordering of canonical [17,"synthetic",id]+LF:
    # A: 6,5,4; B: 8,7; C: 9. Round-robin visits A,B,C,A.
    queue = review_queue(rows, "synthetic", limit_each=4)
    assert queue["stratified"] == [6, 8, 9, 5]
    assert queue["order"] == [1, 6, 2, 8, 3, 9, 10, 5]


def test_duplicate_assay_rows_cannot_appear_twice_in_a_frozen_queue():
    row = {"assay_id": 1, "molecule_count": 2, "bao_format": "F1", "document_year": 2005}
    with pytest.raises(ValueError, match="Duplicate assay"):
        review_queue([row, dict(row)], "synthetic")
def test_sampling_metadata_uses_distinct_source_molecules_without_potency_filtering():
    from assaytrace.review import assay_sampling_rows

    target = {"tid": 93, "chembl_id": "CHEMBL220", "target_type": "SINGLE PROTEIN", "organism": "Homo sapiens"}
    assay = {"assay_id": 1, "tid": 93, "assay_type": "B", "confidence_score": 9,
             "relationship_type": "D", "assay_organism": "Homo sapiens", "doc_id": 5, "bao_format": None}
    raw = {"target": target, "assays": [assay, {**assay, "assay_id": 2, "confidence_score": 8}],
           "activities": [{"assay_id": aid, "molregno": mol, "standard_type": endpoint, "standard_value": None}
                          for aid, mol, endpoint in [(1, 11, "IC50"), (1, 11, "IC50"), (1, 12, "IC50"),
                                                     (1, 13, "Ki"), (2, 14, "IC50")]]}
    assert assay_sampling_rows(raw, [{"doc_id": 5, "year": 2001}]) == [
        {"assay_id": 1, "molecule_count": 2, "bao_format": None, "document_year": 2001}]
