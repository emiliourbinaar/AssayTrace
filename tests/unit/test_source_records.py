from assaytrace.contracts import dedupe_activities
import pytest
from assaytrace.contracts import SourceConflict


def test_deduplicates_encounters_without_collapsing_equal_source_records():
    # Synthetic source records: equal measurements do not prove duplication.
    first = {"source_id": "synthetic", "activity_id": 1,
             "source_payload": {"value": "10"}}
    second = {"source_id": "synthetic", "activity_id": 2,
              "source_payload": {"value": "10"}}

    rows, repeated_encounters = dedupe_activities([first, second, first])

    assert rows == [first, second]
    assert repeated_encounters == 1


def test_conflicting_payload_for_same_source_key_is_rejected():
    first = {"source_id": "synthetic", "activity_id": 1,
             "source_payload": {"value": "10"}}
    changed = {**first, "source_payload": {"value": "20"}}
    with pytest.raises(SourceConflict):
        dedupe_activities([first, changed])


def test_source_payload_preserves_numeric_types_when_checking_conflicts():
    first = {"source_id": "synthetic", "activity_id": 1,
             "source_payload": {"value": 10}}
    changed = {**first, "source_payload": {"value": 10.0}}
    with pytest.raises(SourceConflict):
        dedupe_activities([first, changed])
