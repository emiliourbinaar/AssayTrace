"""Provisional what-if medians, never adopted modeling labels."""
from assaytrace.profile import contrast_support


def test_record_removal_is_distinguished_from_identity_and_prospective_label_changes():
    rows = [
        {"identity_id": "unchanged", "pic50": "8", "potential_duplicate": 0},
        {"identity_id": "unchanged", "pic50": "8", "potential_duplicate": 1},
        {"identity_id": "changed", "pic50": "6", "potential_duplicate": 0},
        {"identity_id": "changed", "pic50": "8", "potential_duplicate": 1},
        {"identity_id": "removed", "pic50": "7", "potential_duplicate": 1},
        {"identity_id": "unknown", "pic50": "9", "potential_duplicate": None},
    ]
    result = contrast_support(rows, {name: name for name in ("unchanged", "changed", "removed", "unknown")}, [])
    assert result is not None
    assert result["removed_training_identities"] == ["removed"]
    assert result["changed_prospective_medians"] == [{"identity_id": "changed", "retain": "7.000000000000", "exclude": "6.000000000000"}]
    assert result["unchanged_shared_training_identities"] == ["unchanged"]
    assert result["removed_training_record_count"] == 3
    assert result["unknown_flag_record_count"] == 1
    assert result["aggregation_status"] == "provisional_what_if_median"


def test_held_out_equivalence_members_are_absent_from_both_training_policies():
    rows = [{"identity_id": identity, "pic50": "8", "potential_duplicate": flag}
            for identity, flag in [("held", 0), ("relative", 1), ("train", 0), ("unknown", None)]]
    mapping = {"held": "g1", "relative": "g1", "train": "g2", "unknown": "g3"}
    result = contrast_support(rows, mapping, ["held", "unknown"])
    assert result["removed_training_identities"] == []
    assert result["retain_training_identities"] == ["train"]
    assert result["exclude_training_identities"] == ["train"]
    assert result["common_reference_identities"] == ["held"]
    assert result["reference_population"] == "restricted_unflagged_not_ground_truth"
    assert result["held_out_group_record_count"] == 3
