"""Offline, authored review snapshots; not evidence of real assay suitability."""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

from assaytrace.review import ReviewContractError, publish_reviews, review_queue


def test_partial_review_can_resume_without_rewriting_the_original_snapshot(tmp_path):
    queue = review_queue([{"assay_id": i, "molecule_count": 10 - i} for i in (1, 2, 3)],
                         "synthetic", limit_each=2)
    first_decision = {"source_id": "synthetic", "assay_id": 1, "category": "unresolved",
                      "confirmation_state": "assistant_proposed", "evidence_refs": ["synthetic:partial"],
                      "record_exceptions": [], "reviewed_at": "time-1"}
    first = publish_reviews(tmp_path, queue, [first_decision])
    assert first is not None
    first_directory = Path(first["manifest_path"]).parent
    original = {path.name: path.read_bytes() for path in first_directory.iterdir()}
    first_review = json.loads((first_directory / "reviews.json").read_bytes())
    assert first_review["unreviewed"] == [3, 2]
    second_decision = {**first_decision, "assay_id": 3, "category": "compatible"}
    resumed = publish_reviews(tmp_path, queue, [first_decision, second_decision])
    resumed_directory = Path(resumed["manifest_path"]).parent
    assert resumed["profile_id"] != first["profile_id"]
    assert json.loads((resumed_directory / "reviews.json").read_bytes())["unreviewed"] == [2]
    assert (resumed_directory / "selection.json").read_bytes() == original["selection.json"]
    assert {path.name: path.read_bytes() for path in first_directory.iterdir()} == original
    reused = publish_reviews(tmp_path, queue, [{**first_decision, "reviewed_at": "time-2"}])
    assert reused["profile_id"] == first["profile_id"]
    assert reused["validation_mode"] == "reconstruction_compared"
    assert Path(reused["run_record"]) != Path(first["run_record"])
    audit = json.loads(Path(reused["run_record"]).read_bytes())
    assert audit["review_audit"][0]["reviewed_at"] == "time-2"


def test_budget_rejection_publishes_nothing_and_corrected_import_can_retry(tmp_path):
    queue = review_queue([{"assay_id": 1, "molecule_count": 10}], "synthetic")
    interval = {"start": "2026-01-01T00:00:00+00:00", "end": "2026-01-01T06:00:01+00:00"}
    with pytest.raises(ReviewContractError, match="budget"):
        publish_reviews(tmp_path, queue, [], intervals=[interval])
    assert list(tmp_path.iterdir()) == []
    result = publish_reviews(tmp_path, queue, [], intervals=[{**interval, "end": "2026-01-01T06:00:00+00:00"}])
    content = json.loads((Path(result["manifest_path"]).parent / "reviews.json").read_bytes())
    assert content["unreviewed"] == [1]
    assert content["decisions"] == []
    audit = json.loads(Path(result["run_record"]).read_bytes())
    assert audit["budget"]["time_cap_reached"] is True
    assert audit["active_intervals"][0]["end"] == "2026-01-01T06:00:00+00:00"


def test_review_import_command_reads_local_files_and_preserves_proposed_status(tmp_path):
    queue = review_queue([{"assay_id": 1, "molecule_count": 10}], "synthetic")
    selection = tmp_path / "selection.json"
    ledger = tmp_path / "ledger.json"
    selection.write_text(json.dumps(queue))
    ledger.write_text(json.dumps({"decisions": [
        {"source_id": "synthetic", "assay_id": 1, "category": "unresolved",
         "confirmation_state": "assistant_proposed", "evidence_refs": ["synthetic:partial"],
         "record_exceptions": []}], "active_intervals": []}))
    output = tmp_path / "output"
    result = subprocess.run(
        [sys.executable, "-m", "assaytrace", "review-import", "--selection", str(selection),
         "--ledger", str(ledger), "--output", str(output)],
        env={**os.environ, "PYTHONPATH": "src"}, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    content = json.loads(next((output / "reviews").glob("*/reviews.json")).read_bytes())
    assert content["decisions"][0]["confirmation_state"] == "assistant_proposed"
    assert json.loads(result.stdout)["manifest_path"]


def test_evidence_linked_early_blocker_preserves_unreviewed_suffix_without_verdict(tmp_path):
    queue = review_queue([{"assay_id": 1, "molecule_count": 10}], "synthetic")
    stop = {"reason": "decisive_blocker", "evidence_refs": ["synthetic:blocker"],
            "explanation": "Authored blocker for import testing only",
            "confirmation_state": "assistant_proposed"}
    result = publish_reviews(tmp_path, queue, [], stop=stop)
    content = json.loads((Path(result["manifest_path"]).parent / "reviews.json").read_bytes())
    assert content.get("stop") == stop
    assert content["unreviewed"] == [1]
    assert "study_feasibility" not in content
    assert json.loads(Path(result["run_record"]).read_bytes())["budget"]["active_seconds"] == 0


def test_review_command_does_not_drop_an_early_stop_from_the_input_ledger(tmp_path):
    from assaytrace.cli import main

    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps(review_queue([{"assay_id": 1, "molecule_count": 10}], "synthetic")))
    stop = {"reason": "decisive_blocker", "evidence_refs": ["synthetic:e1"],
            "explanation": "Synthetic blocker", "confirmation_state": "assistant_proposed"}
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"decisions": [], "active_intervals": [], "stop": stop}))
    output = tmp_path / "output"
    assert main(["review-import", "--selection", str(selection), "--ledger", str(ledger),
                 "--output", str(output)]) == 0
    content = json.loads(next((output / "reviews").glob("*/reviews.json")).read_bytes())
    assert content["stop"] == stop
