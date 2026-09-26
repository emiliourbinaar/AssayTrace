"""Authored reviewed-record inputs; not an actual reviewed scientific population."""
from assaytrace.profile import profile_evidence, molecular_context_profile


def test_diagnostics_keep_quarantined_measurements_and_remove_only_repeated_encounters():
    rows = [{"source_id": "synthetic", "activity_id": i,
             "source_payload": {"activity_id": i, "assay_id": 1, "doc_id": 1, "potential_duplicate": flag},
             "identity_id": identity, "pic50": "8.000000000000",
             "measurement_eligible": True, "allocation_eligible": identity != "quarantined"}
            for i, identity, flag in [(1, "x", 0), (2, "x", 1), (3, "y", 0), (4, "quarantined", 0)]]
    result = profile_evidence([*rows, rows[0]], {"x": "e1", "y": "e2"}, {"x": "s1", "y": "s1"})
    assert result is not None
    content, audit = result
    assert audit["repeated_encounters"] == 1
    assert content["repeat_summary"]["source_record_count"] == 4
    assert content["repeat_summary"]["identities_with_multiple_source_records"] == 1
    assert content["allocation_excluded_measurement_record_count"] == 1
    assert set(content["allocations"]["equivalence"]["identity_to_partition"]) == {"x", "y"}
    assert len(content["allocations"]["scaffold"]["group_to_partition"]) == 1
    assert content["contrasts"]["scaffold"]["removed_training_record_count"] == 1
    assert "conclusions" not in content


def test_source_parent_context_enters_chemistry_and_grouping_without_auxiliary_observations():
    context = {"molecules": [
        {"molecule_id": 1, "source_smiles": "C[NH3+].[Cl-]", "source_parent_claims": [2], "is_candidate": True},
        {"molecule_id": 2, "source_smiles": "CN", "source_parent_claims": [2], "is_candidate": False},
    ], "missing_molecule_ids": []}
    result = molecular_context_profile(context, "synthetic", "chemistry-test", "grouping-test")
    assert result is not None
    molecules, groups = result
    assert molecules[0]["identity_id"] == molecules[1]["identity_id"]
    assert molecules[1]["is_candidate"] is False
    assert all(row["source_id"] == "synthetic" for row in molecules)
    assert len(groups["identity_to_equivalence_group"]) == 1
    assert groups["quarantined_components"] == []
    assert any(edge["reason"] == "source_parent_claim" and edge["parent_molecule_id"] == 2
               for edge in groups["evidence_edges"])
