"""Authored source-shaped examples; confirmation labels here are synthetic test inputs."""
import pytest
import json
from pathlib import Path
from hashlib import sha256

from assaytrace.pipeline import candidate_profile
from assaytrace.artifacts import canonical_json, publish_bundle, read_bundle
from assaytrace.cli import main
from assaytrace.review import assay_sampling_rows, review_queue, publish_reviews


@pytest.fixture
def candidate_inputs():
    raw = {
        "target": {"tid": 93, "chembl_id": "CHEMBL220", "target_type": "SINGLE PROTEIN",
                   "organism": "Homo sapiens"},
        "assays": [{"assay_id": 1, "tid": 93, "assay_type": "B", "confidence_score": 9,
                    "relationship_type": "D", "assay_organism": "Homo sapiens"}],
        "activities": [{"activity_id": i, "assay_id": 1, "molregno": 1, "doc_id": 1,
                        "standard_type": "IC50", "standard_value": "10",
                        "standard_units": "nM", "standard_relation": "=",
                        "data_validity_comment": None, "potential_duplicate": flag}
                       for i, flag in [(1, 0), (2, 1)]],
    }
    context = {"molecules": [{"molecule_id": 1, "source_smiles": "CN",
                              "source_parent_claims": [1], "is_candidate": True}],
               "missing_molecule_ids": []}
    decisions = [{"source_id": "synthetic:pipeline", "assay_id": 1, "category": "compatible",
                  "confirmation_state": "human_confirmed", "evidence_refs": ["synthetic:review"],
                  "record_exceptions": []}]
    return raw, context, decisions


def test_candidate_pipeline_preserves_equal_source_records_and_builds_reviewed_diagnostics(candidate_inputs):
    raw, context, decisions = candidate_inputs
    result = candidate_profile(raw, context, decisions, source_id="synthetic:pipeline",
                               chemistry_digest="test-chemistry", grouping_digest="test-groups")
    assert result is not None
    assert [row["source_payload"] for row in result["activities"]] == raw["activities"]
    assert [row["activity_id"] for row in result["activities"]] == [1, 2]
    assert all(row["pic50"] == "8.000000000000" for row in result["activities"])
    assert all(row["measurement_eligible"] and row["allocation_eligible"] for row in result["activities"])
    assert len({row["identity_id"] for row in result["activities"]}) == 1
    assert result["evidence"]["repeat_summary"]["source_record_count"] == 2
    assert result["evidence"]["repeat_summary"]["identities_with_multiple_source_records"] == 1
    assert result["evidence"]["contrasts"]["equivalence"]["removed_training_record_count"] == 1
    assert result["evidence"]["contrasts"]["equivalence"]["removed_training_identities"] == []
    assert result["evidence"]["contrasts"]["equivalence"]["changed_prospective_medians"] == []
    assert "conclusions" not in result["evidence"]


@pytest.mark.parametrize("field,value,reason", [
    ("standard_relation", ">", "non_exact_relation"),
    ("standard_value", "0", "nonfinite_or_nonpositive_value"),
    ("standard_units", None, "unknown_unit"),
    ("standard_type", "Ki", "wrong_endpoint"),
])
def test_ineligible_numeric_records_remain_auditable_without_aborting_profile(candidate_inputs, field, value, reason):
    raw, context, decisions = candidate_inputs
    raw["activities"][0][field] = value
    try:
        result = candidate_profile(raw, context, decisions, source_id="synthetic:pipeline",
                                   chemistry_digest="test-chemistry", grouping_digest="test-groups")
    except ValueError:
        result = None
    assert result is not None, "Numerically excluded records must not abort profiling"
    excluded = result["activities"][0]
    assert excluded["source_payload"] == raw["activities"][0]
    assert excluded["pic50"] is None
    assert excluded["numerical_reason"] == reason
    assert excluded["measurement_eligible"] is False
    assert result["evidence"]["repeat_summary"]["source_record_count"] == 1


def test_parent_conflict_excludes_allocation_but_retains_reviewed_measurements(candidate_inputs):
    raw, context, decisions = candidate_inputs
    context["molecules"][0]["source_parent_claims"] = [2]
    context["molecules"].append({"molecule_id": 2, "source_smiles": "CO",
                                 "source_parent_claims": [2], "is_candidate": False})
    try:
        result = candidate_profile(raw, context, decisions, source_id="synthetic:pipeline",
                                   chemistry_digest="test-chemistry", grouping_digest="test-groups")
    except KeyError:
        result = None
    assert result is not None, "Quarantined identities must not be sent to allocation"
    assert len(result["activities"]) == 2
    assert all(row["measurement_eligible"] for row in result["activities"])
    assert all(not row["allocation_eligible"] for row in result["activities"])
    assert result["activities"][0]["measurement_reasons"] == []
    assert result["activities"][0]["allocation_reasons"] == ["allocation_quarantine:parent_equivalence_conflict"]
    assert result["evidence"]["repeat_summary"]["source_record_count"] == 2
    assert result["evidence"]["allocation_excluded_measurement_record_count"] == 2
    assert result["evidence"]["allocations"]["scaffold"]["counts"] == {"train": 0, "validation": 0, "test": 0}


def test_repeated_extraction_encounters_do_not_change_scientific_artifacts(candidate_inputs):
    raw, context, decisions = candidate_inputs
    first = candidate_profile(raw, context, decisions, source_id="synthetic:pipeline",
                              chemistry_digest="test-chemistry", grouping_digest="test-groups")
    raw["activities"] = [raw["activities"][1], raw["activities"][0], dict(raw["activities"][0])]
    second = candidate_profile(raw, context, decisions, source_id="synthetic:pipeline",
                               chemistry_digest="test-chemistry", grouping_digest="test-groups")
    assert [row["activity_id"] for row in second["activities"]] == [1, 2]
    assert second["audit"]["repeated_encounters"] == 1
    assert {key: value for key, value in first.items() if key != "audit"} == {
        key: value for key, value in second.items() if key != "audit"}


@pytest.fixture
def candidate_bundle_inputs(candidate_inputs, tmp_path):
    raw, context, decisions = candidate_inputs
    source_id = "synthetic:pipeline"
    root = tmp_path / "inputs"
    candidate = publish_bundle(root, {"source_id": source_id, "target": "CHEMBL220", "endpoint": "IC50"},
                               {"raw-target.json": canonical_json(raw)})
    candidate_sha = sha256(Path(candidate["manifest_path"]).read_bytes()).hexdigest()
    contextual = publish_bundle(root, {"source_id": source_id, "candidate_manifest_sha256": candidate_sha},
                                {"raw-molecules.json": canonical_json(context)})
    sampling = assay_sampling_rows(raw, [])
    queue = review_queue(sampling, source_id)
    selection = publish_bundle(root, {"source_id": source_id, "candidate_manifest_sha256": candidate_sha,
                                      "selection_sha256": queue["selection_sha256"]},
                               {"selection.json": canonical_json(queue), "sampling.json": canonical_json(sampling),
                                "documents.json": canonical_json({"documents": [], "missing_document_ids": []})})
    reviews = publish_reviews(root, queue, decisions)
    descriptor = tmp_path / "inputs.json"
    descriptor.write_bytes(canonical_json({
        "candidate": candidate["manifest_path"], "context": contextual["manifest_path"],
        "selection": selection["manifest_path"], "reviews": reviews["manifest_path"],
    }))
    return descriptor


def test_cli_reconstructs_scientific_artifacts_from_immutable_local_inputs(candidate_bundle_inputs, tmp_path):
    output = tmp_path / "profile-output"
    argv = ["profile", "--inputs", str(candidate_bundle_inputs), "--synthetic", "--output", str(output)]
    try:
        status = main(argv)
    except SystemExit as error:
        status = error.code
    assert status == 0
    manifest_path = next((output / "profiles").glob("*/manifest.json"))
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest["specification"]["profile_contract"] == "candidate-reviewed-v1"
    assert len(manifest["specification"]["processing_code_sha256"]) == 64
    assert set(manifest["specification"]["input_manifest_sha256"]) == {"candidate", "context", "selection", "reviews"}
    evidence = json.loads((manifest_path.parent / "evidence.json").read_bytes())
    assert evidence["repeat_summary"]["source_record_count"] == 2
    summary = json.loads((manifest_path.parent / "summary.json").read_bytes())
    assert summary["source_kind"] == "synthetic"
    assert summary["source_compatibility"] == "not_established"
    assert summary["human_confirmed_assay_count"] == 1
    assert summary["source_record_count"] == 2
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in manifest_path.parent.iterdir()}
    assert main(argv) == 0
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in manifest_path.parent.iterdir()} == before
    runs = [json.loads(path.read_bytes()) for path in (output / "runs").glob("*.json")]
    assert len(runs) == 2
    assert any(run.get("validation_mode") == "reconstruction_compared" for run in runs)


@pytest.mark.parametrize("role,damage", [
    ("context", "source"), ("selection", "source"), ("reviews", "source"),
    ("context", "candidate_link"), ("selection", "candidate_link"),
    ("selection", "queue"), ("reviews", "semantic"),
    ("candidate", "endpoint"), ("candidate", "target"),
])
def test_cli_rejects_incoherent_inputs_even_when_each_bundle_is_intact(candidate_bundle_inputs, tmp_path, role, damage):
    descriptor = json.loads(candidate_bundle_inputs.read_bytes())
    bundle = read_bundle(descriptor[role])
    spec, artifacts = bundle["specification"], bundle["artifacts"]
    if damage == "source":
        spec["source_id"] = "synthetic:different-source"
    elif damage == "candidate_link":
        spec["candidate_manifest_sha256"] = "0" * 64
    elif damage == "queue":
        queue = json.loads(artifacts["selection.json"])
        queue["order"] = [999]
        artifacts["selection.json"] = canonical_json(queue)
    elif damage == "semantic":
        reviews = json.loads(artifacts["reviews.json"])
        reviews["decisions"][0]["category"] = "incompatible"
        artifacts["reviews.json"] = canonical_json(reviews)
    else:
        spec[damage] = "Ki" if damage == "endpoint" else "CHEMBL_OTHER"
    replacement = publish_bundle(tmp_path / "replacement", spec, artifacts)
    descriptor[role] = replacement["manifest_path"]
    candidate_bundle_inputs.write_bytes(canonical_json(descriptor))
    output = tmp_path / "rejected-output"
    with pytest.raises(ValueError):
        main(["profile", "--inputs", str(candidate_bundle_inputs), "--synthetic", "--output", str(output)])
    assert not output.exists()


@pytest.mark.parametrize("state", ["assistant_proposed", "unreviewed"])
def test_cli_reports_unconfirmed_population_without_promoting_decisions(candidate_bundle_inputs, tmp_path, state):
    descriptor = json.loads(candidate_bundle_inputs.read_bytes())
    original = read_bundle(descriptor["reviews"])
    queue = json.loads(original["artifacts"]["selection.json"])
    decisions = json.loads(original["artifacts"]["reviews.json"])["decisions"]
    if state == "unreviewed":
        decisions = []
    else:
        decisions[0]["confirmation_state"] = state
    replacement = publish_reviews(tmp_path / "review-input", queue, decisions)
    descriptor["reviews"] = replacement["manifest_path"]
    candidate_bundle_inputs.write_bytes(canonical_json(descriptor))
    review_path = Path(replacement["manifest_path"])
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in review_path.parent.iterdir()}
    output = tmp_path / "unconfirmed-profile"
    assert main(["profile", "--inputs", str(candidate_bundle_inputs), "--synthetic", "--output", str(output)]) == 0
    path = next((output / "profiles").glob("*/summary.json"))
    summary = json.loads(path.read_bytes())
    assert summary.get("measurement_eligible_record_count") == 0
    assert summary["allocation_eligible_record_count"] == 0
    assert summary["human_confirmed_assay_count"] == 0
    assert summary["assistant_proposed_assay_count"] == (1 if state == "assistant_proposed" else 0)
    assert summary["unreviewed_selected_assay_count"] == (1 if state == "unreviewed" else 0)
    assert summary["scientific_assessment"] == "not_performed"
    evidence = json.loads((path.parent / "evidence.json").read_bytes())
    assert evidence["allocations"]["scaffold"]["counts"] == {"train": 0, "validation": 0, "test": 0}
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in review_path.parent.iterdir()} == before


def test_cli_cannot_label_synthetic_input_as_release_evidence(candidate_bundle_inputs, tmp_path):
    output = tmp_path / "rejected-output"
    with pytest.raises(ValueError):
        main(["profile", "--inputs", str(candidate_bundle_inputs), "--output", str(output)])
    assert not output.exists()


@pytest.mark.parametrize("failure", ["artifact_write", "acknowledgment"])
def test_candidate_cli_recovers_after_interrupted_publication(candidate_bundle_inputs, tmp_path, monkeypatch, failure):
    output = tmp_path / "recovery-output"
    argv = ["profile", "--inputs", str(candidate_bundle_inputs), "--synthetic", "--output", str(output)]
    original_write = Path.write_bytes

    def fail_artifact(path, payload):
        if path.name == "activities.jsonl" and path.parent.name.startswith(".stage-"):
            raise OSError("synthetic storage failure")
        return original_write(path, payload)

    def fail_acknowledgment(*args, **kwargs):
        raise OSError("synthetic acknowledgment failure")

    with monkeypatch.context() as fault:
        if failure == "artifact_write":
            fault.setattr(Path, "write_bytes", fail_artifact)
        else:
            fault.setattr("assaytrace.pipeline.record_run", fail_acknowledgment)
        with pytest.raises(OSError, match="synthetic"):
            main(argv)
    complete = [path for path in (output / "profiles").glob("*/manifest.json")
                if not path.parent.name.startswith(".stage-")]
    assert len(complete) == (1 if failure == "acknowledgment" else 0)
    before = ({p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in complete[0].parent.iterdir()}
              if complete else None)
    assert main(argv) == 0
    complete = [path for path in (output / "profiles").glob("*/manifest.json")
                if not path.parent.name.startswith(".stage-")]
    assert len(complete) == 1
    bundle = read_bundle(complete[0])
    assert len(bundle["artifacts"]["activities.jsonl"].splitlines()) == 2
    if before is not None:
        assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in complete[0].parent.iterdir()} == before
    assert len(list((output / "runs").glob("*.json"))) == 1
