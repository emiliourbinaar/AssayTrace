import json
import sqlite3
import os
import subprocess
import sys

from assaytrace.cli import main
from hashlib import sha256
from pathlib import Path


def test_module_command_executes_the_synthetic_pipeline(synthetic_source, tmp_path):
    output = tmp_path / "command-output"
    result = subprocess.run(
        [sys.executable, "-m", "assaytrace", "profile", "--synthetic",
         "--source", str(synthetic_source), "--output", str(output)],
        env={**os.environ, "PYTHONPATH": "src"}, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert len(list((output / "profiles").glob("*/manifest.json"))) == 1


def test_profile_specification_identifies_code_and_locked_environment(synthetic_source, tmp_path):
    output = tmp_path / "output"
    assert main(["profile", "--source", str(synthetic_source), "--synthetic",
                 "--output", str(output)]) == 0
    manifest = json.loads(next((output / "profiles").glob("*/manifest.json")).read_bytes())
    spec = manifest["specification"]
    assert spec.get("environment_lock_sha256") == sha256(Path("uv.lock").read_bytes()).hexdigest()
    assert spec.get("image_definition_sha256") == sha256(Path("Dockerfile").read_bytes()).hexdigest()
    assert len(spec.get("processing_code_sha256", "")) == 64
    assert spec.get("profile_contract") == "synthetic-numeric-v1"
    assert spec.get("assessment") is None


def test_cli_publishes_accounted_synthetic_profile(synthetic_source, tmp_path):
    output = tmp_path / "output"
    assert main(["profile", "--source", str(synthetic_source), "--synthetic",
                 "--output", str(output)]) == 0
    summaries = list((output / "profiles").glob("*/summary.json"))
    assert len(summaries) == 1
    report = json.loads(summaries[0].read_bytes())
    assert report["source_record_count"] == 6
    assert report["exact_numeric_ic50_count"] == 4
    assert report["source_kind"] == "synthetic"
    assert report["source_compatibility"] == "not_established"
    assert report["study_feasibility"] == "inconclusive"


def test_wrong_source_version_fails_without_publication(synthetic_source, tmp_path):
    with sqlite3.connect(synthetic_source) as db:
        db.execute("UPDATE version SET name='not-approved'")
    output = tmp_path / "output"
    assert main(["profile", "--source", str(synthetic_source), "--synthetic",
                 "--output", str(output)]) == 1
    assert not output.exists()


def test_missing_structure_is_retained_without_component_join_multiplication(synthetic_source, tmp_path):
    output = tmp_path / "output"
    assert main(["profile", "--source", str(synthetic_source), "--synthetic",
                 "--output", str(output)]) == 0
    path = next((output / "profiles").glob("*/activities.jsonl"))
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    assert len(rows) == 6
    assert rows[0].get("source_smiles") == "CCO"
    assert rows[5].get("source_smiles", "absent") is None


def test_cli_retains_source_records_with_numerical_dispositions(synthetic_source, tmp_path):
    output = tmp_path / "output"
    assert main(["profile", "--source", str(synthetic_source), "--synthetic",
                 "--output", str(output)]) == 0
    paths = list((output / "profiles").glob("*/activities.jsonl"))
    assert len(paths) == 1
    rows = [json.loads(line) for line in paths[0].read_bytes().splitlines()]
    assert [r["activity_id"] for r in rows] == [1, 2, 3, 4, 5, 6]
    assert [r["pic50"] for r in rows] == ["8.000000000000", "8.000000000000",
                                         "7.000000000000", None, None, "8.000000000000"]
    assert rows[3]["numerical_reason"] == "wrong_endpoint"
    assert rows[4]["numerical_reason"] == "non_exact_relation"
    assert rows[5]["source_payload"]["potential_duplicate"] is None
    assert all(r["source_id"].startswith("synthetic:") for r in rows)


def test_cli_rerun_keeps_bundle_unchanged_and_records_each_execution(synthetic_source, tmp_path):
    output = tmp_path / "output"
    argv = ["profile", "--source", str(synthetic_source), "--synthetic", "--output", str(output)]
    assert main(argv) == 0
    before = {str(p.relative_to(output)): (p.read_bytes(), p.stat().st_mtime_ns)
              for p in (output / "profiles").rglob("*") if p.is_file()}
    assert main(argv) == 0
    after = {str(p.relative_to(output)): (p.read_bytes(), p.stat().st_mtime_ns)
             for p in (output / "profiles").rglob("*") if p.is_file()}
    assert before == after
    runs = [json.loads(p.read_bytes()) for p in (output / "runs").glob("*.json")]
    assert len(runs) == 2
    assert sorted(r["reused"] for r in runs) == [False, True]


def test_missing_mandatory_column_fails_without_publication(synthetic_source, tmp_path):
    with sqlite3.connect(synthetic_source) as db:
        db.execute("ALTER TABLE activities DROP COLUMN standard_relation")
    output = tmp_path / "output"
    try:
        status = main(["profile", "--source", str(synthetic_source), "--synthetic",
                       "--output", str(output)])
    except KeyError:
        status = "unclassified_missing_column"
    assert status == 1
    assert not output.exists()


def test_profile_records_operative_chemistry_contract_and_digest(synthetic_source, tmp_path):
    output = tmp_path / "output"
    assert main(["profile", "--source", str(synthetic_source), "--synthetic",
                 "--output", str(output)]) == 0
    manifest = json.loads(next((output / "profiles").glob("*/manifest.json")).read_bytes())
    specification = manifest["specification"]
    assert "chemistry_contract" in specification
    contract = specification["chemistry_contract"]
    assert contract["revision"] == "phase1-chemistry-v1"
    assert contract["rdkit_version"] == "2026.03.6"
    assert set(contract["removable_fragments"]) == {
        "O", "[Cl-]", "[Br-]", "[I-]", "[Li+]", "[Na+]", "[K+]", "[Mg+2]", "[Ca+2]"}
    assert contract["uncharger"] == {"canonicalOrder": True, "force": False, "protonationOnly": True}
    serialized = (json.dumps(contract, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    assert specification["chemistry_contract_sha256"] == sha256(serialized).hexdigest()


def test_cli_chemistry_keeps_repeat_records_and_missing_structure_visible(synthetic_source, tmp_path):
    output = tmp_path / "output"
    assert main(["profile", "--source", str(synthetic_source), "--synthetic",
                 "--output", str(output)]) == 0
    directory = next((output / "profiles").iterdir())
    assert (directory / "molecules.jsonl").is_file()
    molecules = [json.loads(line) for line in (directory / "molecules.jsonl").read_bytes().splitlines()]
    activities = [json.loads(line) for line in (directory / "activities.jsonl").read_bytes().splitlines()]
    assert [row["molecule_id"] for row in molecules] == [1, 2, 3]
    assert molecules[2]["reason"] == "missing_structure"
    assert len(activities) == 6
    assert activities[0]["identity_id"] == activities[1]["identity_id"] == molecules[0]["identity_id"]
    assert activities[5]["identity_id"] is None
    summary = json.loads((directory / "summary.json").read_bytes())
    assert summary["exact_numeric_ic50_count"] == 4
    assert summary["exact_numeric_with_structure_count"] == 3
    assert summary["molecular_identity_count"] == 2
    assert summary["assay_review_status"] == "not_assessed"


def test_cli_publishes_explicitly_provisional_synthetic_structure_groups(synthetic_source, tmp_path):
    output = tmp_path / "output"
    assert main(["profile", "--source", str(synthetic_source), "--synthetic",
                 "--output", str(output)]) == 0
    directory = next((output / "profiles").iterdir())
    assert (directory / "groups.json").is_file()
    groups = json.loads((directory / "groups.json").read_bytes())
    molecules = [json.loads(line) for line in (directory / "molecules.jsonl").read_bytes().splitlines()]
    assert set(groups["identity_to_equivalence_group"]) == {molecules[0]["identity_id"], molecules[1]["identity_id"]}
    assert len(set(groups["identity_to_scaffold_group"].values())) == 2
    assert groups["grouping_scope"] == "synthetic_structure_only"
    assert groups["source_parent_assessment"] == "not_assessed"
    assert groups["assay_review_status"] == "not_assessed"
