import pytest

from assaytrace.groups import build_groups


def test_equal_structural_keys_form_order_independent_equivalence_groups():
    molecules = [
        {"molecule_id": "m1", "identity_id": "i1", "structure_equivalence_key": "e1", "scaffold_smiles": "s1"},
        {"molecule_id": "m2", "identity_id": "i2", "structure_equivalence_key": "e1", "scaffold_smiles": "s1"},
        {"molecule_id": "m3", "identity_id": "i3", "structure_equivalence_key": "e2", "scaffold_smiles": "s2"},
    ]
    result = build_groups(molecules, "group-contract")
    assert result is not None
    groups = result["identity_to_equivalence_group"]
    assert groups["i1"] == groups["i2"]
    assert groups["i1"] != groups["i3"]
    assert result == build_groups(list(reversed(molecules)), "group-contract")


def test_unresolved_equivalence_keys_do_not_become_one_usable_null_group():
    molecules = [
        {"molecule_id": "m1", "identity_id": "i1", "structure_equivalence_key": None, "scaffold_smiles": "s1"},
        {"molecule_id": "m2", "identity_id": "i2", "structure_equivalence_key": None, "scaffold_smiles": "s1"},
    ]
    result = build_groups(molecules, "group-contract")
    assert result["identity_to_equivalence_group"] == {}
    assert result["unresolved_identities"] == ["i1", "i2"]


def test_scaffold_groups_union_equivalence_links_transitively():
    molecules = [
        {"molecule_id": "m1", "identity_id": "i1", "structure_equivalence_key": "e1", "scaffold_smiles": "s1"},
        {"molecule_id": "m2", "identity_id": "i2", "structure_equivalence_key": "e1", "scaffold_smiles": "s2"},
        {"molecule_id": "m3", "identity_id": "i3", "structure_equivalence_key": "e2", "scaffold_smiles": "s2"},
        {"molecule_id": "m4", "identity_id": "i4", "structure_equivalence_key": "e3", "scaffold_smiles": "ACYCLIC"},
        {"molecule_id": "m5", "identity_id": "i5", "structure_equivalence_key": "e4", "scaffold_smiles": "ACYCLIC"},
    ]
    result = build_groups(molecules, "group-contract")
    assert "identity_to_scaffold_group" in result
    groups = result["identity_to_scaffold_group"]
    assert groups["i1"] == groups["i2"] == groups["i3"]
    assert groups["i4"] == groups["i5"] != groups["i1"]
    assert result == build_groups(list(reversed(molecules)), "group-contract")


def test_conflicting_parent_quarantines_entire_linked_component_not_measurements():
    molecules = [
        {"molecule_id": "m1", "identity_id": "i1", "structure_equivalence_key": "e1",
         "scaffold_smiles": "s1", "source_parent_claims": ["m2"]},
        {"molecule_id": "m2", "identity_id": "i2", "structure_equivalence_key": "e2",
         "scaffold_smiles": "s2", "source_parent_claims": []},
        {"molecule_id": "m3", "identity_id": "i3", "structure_equivalence_key": "e1",
         "scaffold_smiles": "s1", "source_parent_claims": []},
    ]
    result = build_groups(molecules, "group-contract")
    assert result["identity_to_equivalence_group"] == {}
    assert result["identity_to_scaffold_group"] == {}
    assert result["quarantined_components"] == [
        {"identity_ids": ["i1", "i2", "i3"], "reasons": ["parent_equivalence_conflict"]}
    ]
    assert [row["identity_id"] for row in molecules] == ["i1", "i2", "i3"]


def test_shared_dangling_parent_claim_is_retained_as_a_quarantined_link():
    molecules = [
        {"molecule_id": "m1", "identity_id": "i1", "structure_equivalence_key": "e1",
         "scaffold_smiles": "s1", "source_parent_claims": ["missing"]},
        {"molecule_id": "m2", "identity_id": "i2", "structure_equivalence_key": "e2",
         "scaffold_smiles": "s2", "source_parent_claims": ["missing"]},
    ]
    try:
        result = build_groups(molecules, "group-contract")
    except KeyError:
        result = {}
    assert result.get("quarantined_components") == [
        {"identity_ids": ["i1", "i2"], "reasons": ["dangling_parent"]}
    ]
    assert result["identity_to_equivalence_group"] == {}


def test_parent_with_unresolved_structure_quarantines_child_without_null_identity():
    molecules = [
        {"molecule_id": "child", "identity_id": "i1", "structure_equivalence_key": "e1",
         "scaffold_smiles": "s1", "source_parent_claims": ["parent"]},
        {"molecule_id": "parent", "identity_id": None, "structure_equivalence_key": None,
         "scaffold_smiles": None, "source_parent_claims": []},
    ]
    try:
        result = build_groups(molecules, "group-contract")
    except KeyError:
        result = {}
    assert result.get("quarantined_components") == [
        {"identity_ids": ["i1"], "reasons": ["parent_structure_unresolved"]}
    ]
    assert result["identity_to_equivalence_group"] == {}
    assert None not in result["unresolved_identities"]


def test_multiple_parent_claims_are_quarantined_even_when_structures_agree():
    molecules = [
        {"molecule_id": name, "identity_id": "i1", "structure_equivalence_key": "e1",
         "scaffold_smiles": "s1", "source_parent_claims": parents}
        for name, parents in [("child", ["p1", "p2"]), ("p1", []), ("p2", [])]
    ]
    result = build_groups(molecules, "group-contract")
    assert result["identity_to_equivalence_group"] == {}
    assert result["quarantined_components"] == [
        {"identity_ids": ["i1"], "reasons": ["multiple_parent_claims"]}
    ]


def test_nonself_parent_cycle_is_quarantined_but_self_parent_is_valid():
    cycle = [
        {"molecule_id": name, "identity_id": "i1", "structure_equivalence_key": "e1",
         "scaffold_smiles": "s1", "source_parent_claims": [parent]}
        for name, parent in [("m1", "m2"), ("m2", "m1")]
    ]
    result = build_groups(cycle, "group-contract")
    assert result["identity_to_equivalence_group"] == {}
    assert result["quarantined_components"] == [
        {"identity_ids": ["i1"], "reasons": ["parent_cycle"]}
    ]
    self_parent = [dict(cycle[0], source_parent_claims=["m1"])]
    valid = build_groups(self_parent, "group-contract")
    assert list(valid["identity_to_equivalence_group"]) == ["i1"]
    assert valid["quarantined_components"] == []


def test_parent_only_identity_connects_evidence_without_becoming_an_observation():
    molecules = [
        {"molecule_id": "child", "identity_id": "i1", "structure_equivalence_key": "e1",
         "scaffold_smiles": "s1", "source_parent_claims": ["parent"], "is_candidate": True},
        {"molecule_id": "parent", "identity_id": "i2", "structure_equivalence_key": "e1",
         "scaffold_smiles": "s1", "source_parent_claims": ["parent"], "is_candidate": False},
    ]
    result = build_groups(molecules, "group-contract")
    assert set(result["identity_to_equivalence_group"]) == {"i1"}
    assert set(result["identity_to_scaffold_group"]) == {"i1"}
    assert result["quarantined_components"] == []


def test_unresolved_child_equivalence_cannot_hide_a_parent_link():
    molecules = [
        {"molecule_id": "child", "identity_id": "i1", "structure_equivalence_key": None,
         "scaffold_smiles": "s1", "source_parent_claims": ["parent"]},
        {"molecule_id": "parent", "identity_id": "i2", "structure_equivalence_key": "e1",
         "scaffold_smiles": "s1", "source_parent_claims": []},
    ]
    try:
        result = build_groups(molecules, "group-contract")
    except KeyError:
        result = {}
    assert result.get("quarantined_components") == [
        {"identity_ids": ["i1", "i2"], "reasons": ["parent_equivalence_unresolved"]}
    ]
    assert result["identity_to_equivalence_group"] == {}
    assert result["unresolved_identities"] == ["i1"]


def test_distinct_missing_child_identities_do_not_create_a_shared_null_bridge():
    molecules = [
        {"molecule_id": "c1", "identity_id": None, "structure_equivalence_key": None,
         "scaffold_smiles": None, "source_parent_claims": ["p1"]},
        {"molecule_id": "c2", "identity_id": None, "structure_equivalence_key": None,
         "scaffold_smiles": None, "source_parent_claims": ["p2"]},
        {"molecule_id": "p1", "identity_id": "i1", "structure_equivalence_key": "e1",
         "scaffold_smiles": "s1", "source_parent_claims": []},
        {"molecule_id": "p2", "identity_id": "i2", "structure_equivalence_key": "e2",
         "scaffold_smiles": "s2", "source_parent_claims": []},
    ]
    try:
        result = build_groups(molecules, "group-contract")
    except TypeError:
        result = {}
    assert result.get("quarantined_components") == [
        {"identity_ids": ["i1"], "reasons": ["parent_equivalence_unresolved"]},
        {"identity_ids": ["i2"], "reasons": ["parent_equivalence_unresolved"]},
    ]


def test_source_parent_edges_retain_release_and_claim_provenance():
    molecules = [
        {"source_id": "synthetic-release", "molecule_id": "child", "identity_id": "i1",
         "structure_equivalence_key": "e1", "scaffold_smiles": "s1", "source_parent_claims": ["missing"]},
    ]
    result = build_groups(molecules, "group-contract")
    assert result.get("evidence_edges") == [{
        "reason": "source_parent_claim", "source_id": "synthetic-release",
        "source_molecule_id": "child", "parent_molecule_id": "missing",
    }]


def test_structural_and_scaffold_edges_explain_transitive_grouping():
    molecules = [
        {"molecule_id": "m1", "identity_id": "i1", "structure_equivalence_key": "e1", "scaffold_smiles": "s1"},
        {"molecule_id": "m2", "identity_id": "i2", "structure_equivalence_key": "e1", "scaffold_smiles": "s2"},
        {"molecule_id": "m3", "identity_id": "i3", "structure_equivalence_key": "e2", "scaffold_smiles": "s2"},
    ]
    edges = build_groups(molecules, "group-contract")["evidence_edges"]
    assert {tuple(sorted(edge.items())) for edge in edges} == {
        tuple(sorted({"reason": "structure_equivalence", "from_identity": "i1",
                      "to_identity": "i2", "structure_equivalence_key": "e1"}.items())),
        tuple(sorted({"reason": "scaffold", "from_identity": "i2",
                      "to_identity": "i3", "scaffold_smiles": "s2"}.items())),
    }


def test_review_projection_preserves_full_universe_bridges_and_group_ids():
    molecules = [
        {"molecule_id": "m1", "identity_id": "i1", "structure_equivalence_key": "e1", "scaffold_smiles": "s1"},
        {"molecule_id": "m2", "identity_id": "i2", "structure_equivalence_key": "e1", "scaffold_smiles": "s2"},
        {"molecule_id": "m3", "identity_id": "i3", "structure_equivalence_key": "e2", "scaffold_smiles": "s2"},
    ]
    full = build_groups(molecules, "group-contract")
    projected = build_groups(molecules, "group-contract", selected_identity_ids={"i1", "i3"})
    assert set(projected["identity_to_scaffold_group"]) == {"i1", "i3"}
    assert projected["identity_to_scaffold_group"]["i1"] == projected["identity_to_scaffold_group"]["i3"]
    assert projected["identity_to_scaffold_group"]["i1"] == full["identity_to_scaffold_group"]["i1"]
    assert projected["evidence_edges"] == full["evidence_edges"]
