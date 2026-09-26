"""Authored active-time intervals, not a record of review actually performed."""
import pytest

from assaytrace.review import ReviewContractError, review_budget


def test_review_budget_counts_document_time_inside_total_and_accepts_exact_caps():
    result = review_budget([
        {"start": "2026-01-01T00:00:00+00:00", "end": "2026-01-01T00:10:00+00:00", "document_id": 1},
        {"start": "2026-01-01T00:10:00+00:00", "end": "2026-01-01T06:00:00+00:00"},
    ])
    assert result == {"active_seconds": 21600, "document_seconds": {"1": 600},
                      "document_count": 1, "time_cap_reached": True}


@pytest.mark.parametrize("intervals", [
    [{"start": "2026-01-01T00:00:00+00:00", "end": "2026-01-01T06:00:01+00:00"}],
    [{"start": "2026-01-01T00:00:00+00:00", "end": "2026-01-01T00:10:01+00:00", "document_id": 1}],
    [{"start": f"2026-01-01T00:{i:02}:00+00:00", "end": f"2026-01-01T00:{i:02}:01+00:00",
      "document_id": i} for i in range(21)],
    [{"start": "2026-01-01T00:00:01+00:00", "end": "2026-01-01T00:00:00+00:00"}],
    [{"start": "2026-01-01T00:00:00", "end": "2026-01-01T00:01:00"}],
    [{"start": "2026-01-01T00:00:00+00:00", "end": "2026-01-01T00:02:00+00:00"},
     {"start": "2026-01-01T00:01:00+00:00", "end": "2026-01-01T00:03:00+00:00"}],
])
def test_invalid_or_excessive_active_time_cannot_enter_the_review_audit(intervals):
    with pytest.raises(ReviewContractError):
        review_budget(intervals)
