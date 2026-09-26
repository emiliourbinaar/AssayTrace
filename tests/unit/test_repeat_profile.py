"""Authored source records, with no claim of experimental independence."""
from assaytrace.profile import repeat_summary, repeat_details


def test_equal_valued_distinct_source_records_remain_in_repeat_counts():
    rows = [{"source_id": "synthetic", "activity_id": i, "identity_id": "x",
             "assay_id": 1, "document_id": 1, "pic50": "8.000000000000",
             "potential_duplicate": flag} for i, flag in [(1, 0), (2, 1), (3, 0)]]
    result = repeat_summary(rows)
    assert result == {"source_record_count": 3, "source_flagged_count": 1,
                      "source_unflagged_count": 2, "source_unknown_flag_count": 0,
                      "identities_with_multiple_source_records": 1}
    assert len(rows) == 3


def test_repeat_details_describe_source_provenance_and_dispersion_without_collapsing_values():
    rows = [{"source_id": "synthetic", "activity_id": i, "identity_id": "x",
             "assay_id": assay, "document_id": 7, "pic50": value,
             "potential_duplicate": None} for i, assay, value in [(1, 1, "8"), (2, 2, "6"), (3, 2, "8")]]
    assert repeat_details(rows) == [{
        "identity_id": "x", "source_record_count": 3, "source_assay_count": 2,
        "source_document_count": 1, "distinct_numeric_value_count": 2,
        "missing_assay_record_count": 0, "missing_document_record_count": 0,
        "minimum_pic50": "6.000000000000", "maximum_pic50": "8.000000000000",
        "range_pic50": "2.000000000000",
    }]


def test_missing_provenance_is_reported_as_missing_not_as_a_distinct_source():
    rows = [{"identity_id": "x", "assay_id": assay, "document_id": document, "pic50": "7"}
            for assay, document in [(None, None), (1, 3), (1, None)]]
    result = repeat_details(rows)[0]
    assert result["source_assay_count"] == 1
    assert result["source_document_count"] == 1
    assert result["missing_assay_record_count"] == 1
    assert result["missing_document_record_count"] == 2
