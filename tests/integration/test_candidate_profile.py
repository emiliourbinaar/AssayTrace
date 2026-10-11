"""Authored source-shaped examples; confirmation labels here are synthetic test inputs."""
import pytest
import json
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import importlib

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
    failed_runs = [json.loads(path.read_bytes()) for path in (output / "runs").glob("*.json")]
    assert len(failed_runs) == (1 if failure == "artifact_write" else 0)
    if failure == "artifact_write":
        assert failed_runs[0]["status"] == "failed"
        assert failed_runs[0]["error_type"] == "OSError"
        assert "manifest_path" not in failed_runs[0]
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
    assert len(list((output / "runs").glob("*.json"))) == (2 if failure == "artifact_write" else 1)


@pytest.mark.parametrize("mode,module_name,operation", [
    ("candidate", "assaytrace.pipeline", "candidate_profile"),
    ("synthetic", "assaytrace.cli", "extract_synthetic"),
    ("review", "assaytrace.review", "review_budget"),
])
def test_cli_run_timestamps_enclose_actual_processing(candidate_bundle_inputs, candidate_inputs,
                                                     synthetic_source, tmp_path, monkeypatch,
                                                     mode, module_name, operation):
    output = tmp_path / "timed-output"
    if mode == "candidate":
        argv = ["profile", "--inputs", str(candidate_bundle_inputs), "--synthetic", "--output", str(output)]
    elif mode == "synthetic":
        argv = ["profile", "--source", str(synthetic_source), "--synthetic", "--output", str(output)]
    else:
        descriptor = json.loads(candidate_bundle_inputs.read_bytes())
        selection = Path(descriptor["selection"]).parent / "selection.json"
        ledger = tmp_path / "ledger.json"
        ledger.write_bytes(canonical_json({"decisions": candidate_inputs[2], "active_intervals": []}))
        argv = ["review-import", "--selection", str(selection), "--ledger", str(ledger), "--output", str(output)]
    module = importlib.import_module(module_name)
    original = getattr(module, operation)
    observed = []

    def timed_operation(*args, **kwargs):
        begin = datetime.now(timezone.utc)
        result = original(*args, **kwargs)
        observed.append((begin, datetime.now(timezone.utc)))
        return result

    monkeypatch.setattr(module, operation, timed_operation)
    assert main(argv) == 0
    record = json.loads(next((output / "runs").glob("*.json")).read_bytes())
    assert record["started_at"] is not None
    assert record["finished_at"] is not None
    start, finish = (datetime.fromisoformat(record[key]) for key in ("started_at", "finished_at"))
    assert start <= observed[0][0] <= observed[0][1] <= finish <= datetime.fromisoformat(record["recorded_at"])


@pytest.mark.parametrize("exception_activity_id", [2, 999])
def test_profile_rejects_review_exceptions_that_do_not_resolve_to_the_reviewed_assay(candidate_inputs,
                                                                                  exception_activity_id):
    raw, context, decisions = candidate_inputs
    raw["activities"][1]["assay_id"] = 2
    raw["assays"].append({**raw["assays"][0], "assay_id": 2})
    decisions[0]["record_exceptions"] = [{"activity_id": exception_activity_id,
                                         "reason": "synthetic_record_contradiction",
                                         "evidence_refs": ["synthetic:exception"]}]
    with pytest.raises(ValueError, match="exception.*assay"):
        candidate_profile(raw, context, decisions, source_id="synthetic:pipeline",
                          chemistry_digest="test-chemistry", grouping_digest="test-groups")


@pytest.fixture
def assessment_inputs(candidate_bundle_inputs, tmp_path):
    output = tmp_path / "evidence-profile"
    assert main(["profile", "--inputs", str(candidate_bundle_inputs), "--synthetic",
                 "--output", str(output)]) == 0
    manifest = next((output / "profiles").glob("*/manifest.json"))
    ledger = {
        "profile_manifest_sha256": sha256(manifest.read_bytes()).hexdigest(),
        "criteria": {name: {
            "status": "inconclusive", "evidence_refs": ["summary.json", "evidence.json"],
            "limitations": ["Authored synthetic evidence only"], "scope": "Synthetic population",
            "reviewer_confirmation": "assistant_proposed", "next_action": "Review actual source evidence",
        } for name in ("population", "allocation", "curation")},
        "exit_narrative": "Synthetic example; no actual feasibility finding.",
        "audit": {"reviewer": "synthetic actor", "reviewed_at": "2026-01-01T00:00:00Z"},
    }
    path = tmp_path / "assessment-ledger.json"
    path.write_bytes(canonical_json(ledger))
    return manifest, path, ledger


def test_assess_cli_publishes_explicit_criteria_bound_to_immutable_evidence(assessment_inputs, tmp_path):
    manifest, ledger_path, ledger = assessment_inputs
    original = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in manifest.parent.iterdir()}
    output = tmp_path / "assessment-output"
    try:
        status = main(["assess", "--profile", str(manifest), "--ledger", str(ledger_path),
                       "--synthetic", "--output", str(output)])
    except SystemExit as error:
        status = error.code
    assert status == 0, "The local assess command must accept an explicit, evidence-bound criterion ledger"
    assessed = read_bundle(next((output / "profiles").glob("*/manifest.json")))
    assessment = json.loads(assessed["artifacts"]["assessment.json"])
    assert assessment == {"criteria": ledger["criteria"], "exit_narrative": ledger["exit_narrative"],
                          "conclusions": {"prediction": "inconclusive", "study": "inconclusive"},
                          "confirmation_state": "assistant_proposed"}
    assert assessed["specification"]["evidence_manifest_sha256"] == ledger["profile_manifest_sha256"]
    assert assessed["specification"]["assessment"] == sha256(canonical_json(assessment)).hexdigest()
    assert json.loads(assessed["artifacts"]["summary.json"])["scientific_assessment"] == "assistant_proposed"
    for name in ("activities.jsonl", "molecules.jsonl", "groups.json", "evidence.json"):
        assert assessed["artifacts"][name] == original[name][0]
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in manifest.parent.iterdir()} == original
    run = json.loads(next((output / "runs").glob("*.json")).read_bytes())
    assert run["assessment_audit"] == ledger["audit"]


def test_assess_cli_rejects_ledger_bound_to_another_profile(assessment_inputs, tmp_path):
    manifest, ledger_path, ledger = assessment_inputs
    ledger["profile_manifest_sha256"] = "0" * 64
    ledger_path.write_bytes(canonical_json(ledger))
    output = tmp_path / "assessment-output"
    with pytest.raises(ValueError, match="profile.*digest"):
        main(["assess", "--profile", str(manifest), "--ledger", str(ledger_path),
              "--synthetic", "--output", str(output)])
    assert not list(output.rglob("manifest.json"))


@pytest.mark.parametrize("source_id,synthetic", [
    ("synthetic:pipeline", False),
    ("ChEMBL37:33c203740555f96067710cdfc1c3c55d890660e5908ec5cbf5817492c290d281", True),
    ("ChEMBL99:unapproved", False),
])
def test_assess_cli_rejects_source_mode_mismatch(assessment_inputs, tmp_path, source_id, synthetic):
    manifest, ledger_path, ledger = assessment_inputs
    original = read_bundle(manifest)
    changed = publish_bundle(tmp_path / "other-input", {**original["specification"], "source_id": source_id},
                             original["artifacts"])
    manifest = Path(changed["manifest_path"])
    ledger["profile_manifest_sha256"] = sha256(manifest.read_bytes()).hexdigest()
    ledger_path.write_bytes(canonical_json(ledger))
    output = tmp_path / "assessment-output"
    argv = ["assess", "--profile", str(manifest), "--ledger", str(ledger_path), "--output", str(output)]
    if synthetic:
        argv.append("--synthetic")
    with pytest.raises(ValueError, match="source identity"):
        main(argv)
    assert not list(output.rglob("manifest.json"))


@pytest.mark.parametrize("section,field,value", [
    ("population", "evidence_refs", ["missing.json"]),
    ("population", "evidence_refs", [123]),
    ("curation", "scope", "   "),
    ("curation", "limitations", [None]),
    ("allocation", "reviewer", "must live in the audit"),
    (None, "exit_narrative", ""),
    (None, "unexpected_metadata", "do not silently ignore fields"),
])
def test_assess_cli_rejects_unresolved_or_malformed_evidence(assessment_inputs, tmp_path, section, field, value):
    manifest, ledger_path, ledger = assessment_inputs
    target = ledger if section is None else ledger["criteria"][section]
    target[field] = value
    ledger_path.write_bytes(canonical_json(ledger))
    output = tmp_path / "assessment-output"
    with pytest.raises(ValueError, match="Assessment"):
        main(["assess", "--profile", str(manifest), "--ledger", str(ledger_path),
              "--synthetic", "--output", str(output)])
    assert not list(output.rglob("manifest.json"))


@pytest.mark.parametrize("contract", ["synthetic-numeric-v1", "candidate-assessed-v1"])
def test_assess_cli_requires_a_complete_unassessed_candidate_profile(assessment_inputs, tmp_path, contract):
    manifest, ledger_path, ledger = assessment_inputs
    original = read_bundle(manifest)
    changed = publish_bundle(tmp_path / "other-input", {**original["specification"], "profile_contract": contract},
                             original["artifacts"])
    manifest = Path(changed["manifest_path"])
    ledger["profile_manifest_sha256"] = sha256(manifest.read_bytes()).hexdigest()
    ledger_path.write_bytes(canonical_json(ledger))
    output = tmp_path / "assessment-output"
    with pytest.raises(ValueError, match="unassessed candidate"):
        main(["assess", "--profile", str(manifest), "--ledger", str(ledger_path),
              "--synthetic", "--output", str(output)])
    assert not list(output.rglob("manifest.json"))


def test_assess_cli_audits_publication_failure_and_recovers(assessment_inputs, tmp_path, monkeypatch):
    manifest, ledger_path, _ = assessment_inputs
    output = tmp_path / "assessment-output"
    argv = ["assess", "--profile", str(manifest), "--ledger", str(ledger_path),
            "--synthetic", "--output", str(output)]
    original_write = Path.write_bytes

    def fail_assessment(path, payload):
        if path.name == "assessment.json" and path.parent.name.startswith(".stage-"):
            raise OSError("synthetic assessment storage failure")
        return original_write(path, payload)

    with monkeypatch.context() as fault:
        fault.setattr(Path, "write_bytes", fail_assessment)
        with pytest.raises(OSError, match="synthetic assessment"):
            main(argv)
    assert not list((output / "profiles").glob("*/manifest.json"))
    failures = [json.loads(path.read_bytes()) for path in (output / "runs").glob("*.json")]
    assert len(failures) == 1
    assert failures[0]["status"] == "failed"
    assert failures[0]["error_type"] == "OSError"
    assert "manifest_path" not in failures[0]
    assert main(argv) == 0
    complete = list((output / "profiles").glob("*/manifest.json"))
    assert len(complete) == 1
    assert read_bundle(complete[0])["profile_id"] == failures[0]["profile_id"]
    assert len(list((output / "runs").glob("*.json"))) == 2


def test_assessment_identity_excludes_audit_but_changes_with_scientific_amendments(assessment_inputs, tmp_path):
    manifest, ledger_path, ledger = assessment_inputs
    output = tmp_path / "assessment-output"
    argv = ["assess", "--profile", str(manifest), "--ledger", str(ledger_path),
            "--synthetic", "--output", str(output)]
    assert main(argv) == 0
    original = next((output / "profiles").glob("*/manifest.json"))
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in original.parent.iterdir()}
    ledger["audit"] = {"reviewer": "another synthetic actor", "reviewed_at": "2026-02-01T00:00:00Z"}
    ledger_path.write_bytes(canonical_json(ledger))
    assert main(argv) == 0
    assert list((output / "profiles").glob("*/manifest.json")) == [original]
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in original.parent.iterdir()} == before
    runs = [json.loads(path.read_bytes()) for path in (output / "runs").glob("*.json")]
    reused = next(row for row in runs if row["reused"])
    assert reused["validation_mode"] == "reconstruction_compared"
    assert reused["assessment_audit"] == ledger["audit"]
    ledger["exit_narrative"] += " Documented synthetic amendment."
    ledger_path.write_bytes(canonical_json(ledger))
    assert main(argv) == 0
    assert len(list((output / "profiles").glob("*/manifest.json"))) == 2
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in original.parent.iterdir()} == before


@pytest.mark.parametrize("status", ["supported", "not_supported"])
def test_assess_cli_never_promotes_unconfirmed_decisive_criteria(assessment_inputs, tmp_path, status):
    manifest, ledger_path, ledger = assessment_inputs
    ledger["criteria"]["population"]["status"] = status
    ledger_path.write_bytes(canonical_json(ledger))
    output = tmp_path / "assessment-output"
    with pytest.raises(ValueError, match="unconfirmed scientific criterion"):
        main(["assess", "--profile", str(manifest), "--ledger", str(ledger_path),
              "--synthetic", "--output", str(output)])
    assert not list(output.rglob("manifest.json"))
