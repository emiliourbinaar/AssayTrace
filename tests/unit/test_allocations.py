"""Hand-derived allocation diagnostics, not model training splits."""
from assaytrace.groups import allocate_groups


def test_whole_groups_are_greedily_allocated_against_identity_count_targets():
    mapping = {**{f"a{i}": "large" for i in range(7)}, "b1": "medium", "b2": "medium", "c": "small"}
    result = allocate_groups(mapping)
    assert result is not None
    assert result["group_to_partition"] == {"large": "train", "medium": "validation", "small": "test"}
    assert result["counts"] == {"train": 7, "validation": 2, "test": 1}
    assert result["target_counts"] == {"train": "7", "validation": "3/2", "test": "3/2"}
    assert result["identity_to_partition"]["b1"] == result["identity_to_partition"]["b2"] == "validation"


def test_equal_size_group_allocation_is_invariant_to_input_order():
    mapping = {f"i{i}": f"g{i}" for i in range(10)}
    forward = allocate_groups(mapping)
    reverse = allocate_groups(dict(reversed(list(mapping.items()))))
    assert forward == reverse
    assert forward["counts"] == {"train": 7, "validation": 2, "test": 1}


def test_dominant_group_reports_empty_partitions_without_splitting_or_verdict():
    result = allocate_groups({"a": "one", "b": "one", "c": "one"})
    assert result.get("empty_partitions") == ["validation", "test"]
    assert result["counts"] == {"train": 3, "validation": 0, "test": 0}
    assert set(result["identity_to_partition"].values()) == {"train"}
    assert "feasibility" not in result
