import json
from pathlib import Path
import pytest
import os
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from assaytrace.artifacts import BundleIntegrityError, publish_bundle, record_run


def test_publication_writes_artifact_and_completion_manifest(tmp_path):
    specification = {"source_id": "synthetic", "contract": "test-v1"}
    payload = b'{"source_record_count":2}\n'
    result = publish_bundle(tmp_path, specification, {"summary.json": payload})
    assert result is not None
    manifest_path = Path(result["manifest_path"])
    assert manifest_path.is_file()
    assert (manifest_path.parent / "summary.json").read_bytes() == payload
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest["specification"] == specification
    assert manifest["artifacts"]["summary.json"]["size"] == len(payload)
    assert result["reused"] is False


def test_identical_rerun_preserves_every_file_and_modification_time(tmp_path):
    spec = {"source_id": "synthetic"}
    artifacts = {"summary.json": b'{"count":2}\n'}
    first = publish_bundle(tmp_path, spec, artifacts)
    directory = Path(first["manifest_path"]).parent
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in directory.iterdir()}
    try:
        second = publish_bundle(tmp_path, spec, artifacts)
    except FileExistsError:
        second = {"reused": False}
    assert second["reused"] is True
    assert second["profile_id"] == first["profile_id"]
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in directory.iterdir()} == before


def test_extra_incoming_artifact_is_rejected(tmp_path):
    spec = {"source_id": "synthetic"}
    publish_bundle(tmp_path, spec, {"summary.json": b"{}\n"})
    with pytest.raises(BundleIntegrityError):
        publish_bundle(tmp_path, spec, {"summary.json": b"{}\n", "extra.json": b"{}\n"})


def test_failed_artifact_write_never_exposes_a_final_directory(tmp_path, monkeypatch):
    original = Path.write_bytes

    def fail_summary(path, payload):
        if path.name == "summary.json":
            raise OSError("synthetic disk failure")
        return original(path, payload)

    monkeypatch.setattr(Path, "write_bytes", fail_summary)
    with pytest.raises(OSError, match="synthetic disk failure"):
        publish_bundle(tmp_path, {"source_id": "synthetic"}, {"summary.json": b"{}\n"})
    assert [p for p in tmp_path.iterdir() if not p.name.startswith(".stage-")] == []


def test_sync_failure_prevents_publication(tmp_path, monkeypatch):
    def fail_sync(descriptor):
        raise OSError("synthetic fsync failure")

    monkeypatch.setattr(os, "fsync", fail_sync)
    with pytest.raises(OSError, match="synthetic fsync failure"):
        publish_bundle(tmp_path, {"source_id": "synthetic"}, {"summary.json": b"{}\n"})
    assert [p for p in tmp_path.iterdir() if not p.name.startswith(".stage-")] == []


@pytest.mark.parametrize("name", ["../escape.json", "/tmp/escape.json", "manifest.json", "sub/file.json"])
def test_unsafe_or_reserved_artifact_names_are_rejected_before_writes(tmp_path, name):
    try:
        publish_bundle(tmp_path, {"source_id": "synthetic"}, {name: b"{}\n"})
    except ValueError as error:
        reason = str(error)
    except OSError:
        reason = "unclassified_filesystem_error"
    else:
        reason = "accepted"
    assert reason == "invalid_artifact_name"
    assert list(tmp_path.iterdir()) == []


def test_manifest_specification_mismatch_is_rejected(tmp_path):
    spec = {"source_id": "synthetic"}
    artifacts = {"summary.json": b"{}\n"}
    result = publish_bundle(tmp_path, spec, artifacts)
    path = Path(result["manifest_path"])
    manifest = json.loads(path.read_bytes())
    manifest["specification"] = {"source_id": "different"}
    path.write_text(json.dumps(manifest))
    with pytest.raises(BundleIntegrityError):
        publish_bundle(tmp_path, spec, artifacts)


def test_run_records_are_distinct_and_outside_immutable_bundle(tmp_path):
    result = publish_bundle(tmp_path / "profiles", {"source_id": "synthetic"}, {"summary.json": b"{}\n"})
    first = record_run(tmp_path / "runs", result)
    second = record_run(tmp_path / "runs", result)
    assert first is not None and second is not None
    assert first != second
    records = [json.loads(Path(p).read_bytes()) for p in (first, second)]
    assert all(r["profile_id"] == result["profile_id"] for r in records)
    assert all("started_at" in r and "manifest_sha256" in r for r in records)
    assert all(Path(p).parent == tmp_path / "runs" for p in (first, second))


@pytest.mark.parametrize("timing", [None, {
    "started_at": "2020-01-01T00:00:00+00:00", "finished_at": "2020-01-01T00:00:02+00:00",
}])
def test_run_audit_keeps_execution_timing_separate_from_acknowledgment(tmp_path, timing):
    result = publish_bundle(tmp_path / "profiles", {"source_id": "synthetic"}, {"summary.json": b"{}\n"})
    before = datetime.now(timezone.utc)
    path = record_run(tmp_path / "runs", {**result, **(timing or {})})
    after = datetime.now(timezone.utc)
    record = json.loads(Path(path).read_bytes())
    assert record.get("started_at") == (timing["started_at"] if timing else None)
    assert record.get("finished_at") == (timing["finished_at"] if timing else None)
    assert before <= datetime.fromisoformat(record["recorded_at"]) <= after


def test_failed_run_can_be_recorded_without_inventing_a_completed_bundle(tmp_path):
    result = {"status": "failed", "profile_id": "synthetic-specification-id",
              "error_type": "OSError", "error_message": "synthetic disk failure",
              "started_at": "2020-01-01T00:00:00+00:00", "finished_at": "2020-01-01T00:00:01+00:00"}
    try:
        path = record_run(tmp_path / "runs", result)
    except KeyError:
        path = None
    assert path is not None, "Failed runs have no completion manifest to hash"
    record = json.loads(Path(path).read_bytes())
    assert record["status"] == "failed"
    assert record["error_type"] == "OSError"
    assert record["error_message"] == "synthetic disk failure"
    assert "manifest_path" not in record and "manifest_sha256" not in record
    assert not (tmp_path / "profiles").exists()


def test_manifest_records_logical_hash_and_row_count_for_jsonl(tmp_path):
    payload = b'{"activity_id":1}\n{"activity_id":2}\n'
    result = publish_bundle(tmp_path, {"source_id": "synthetic"}, {"activities.jsonl": payload})
    metadata = json.loads(Path(result["manifest_path"]).read_bytes())["artifacts"]["activities.jsonl"]
    assert metadata.get("row_count") == 2
    assert metadata.get("logical_sha256") == metadata["sha256"]
    assert metadata.get("equality") == "canonical_bytes"


def test_summary_json_has_declared_logical_equality(tmp_path):
    result = publish_bundle(tmp_path, {"source_id": "synthetic"}, {"summary.json": b"{}\n"})
    metadata = json.loads(Path(result["manifest_path"]).read_bytes())["artifacts"]["summary.json"]
    assert metadata.get("row_count") == 1
    assert metadata.get("logical_sha256") == metadata["sha256"]
    assert metadata.get("equality") == "canonical_bytes"


def test_summary_logical_metadata_is_verified_on_reuse(tmp_path):
    spec = {"source_id": "synthetic"}
    data = {"summary.json": b"{}\n"}
    result = publish_bundle(tmp_path, spec, data)
    path = Path(result["manifest_path"])
    manifest = json.loads(path.read_bytes())
    manifest["artifacts"]["summary.json"]["logical_sha256"] = "0" * 64
    path.write_text(json.dumps(manifest))
    with pytest.raises(BundleIntegrityError):
        publish_bundle(tmp_path, spec, data)


def test_rerun_rejects_incorrect_stored_logical_metadata(tmp_path):
    artifacts = {"activities.jsonl": b'{"activity_id":1}\n'}
    spec = {"source_id": "synthetic"}
    result = publish_bundle(tmp_path, spec, artifacts)
    path = Path(result["manifest_path"])
    manifest = json.loads(path.read_bytes())
    manifest["artifacts"]["activities.jsonl"]["row_count"] = 20
    path.write_text(json.dumps(manifest))
    with pytest.raises(BundleIntegrityError):
        publish_bundle(tmp_path, spec, artifacts)


def test_recomputed_reuse_reports_actual_comparison(tmp_path):
    spec = {"source_id": "synthetic"}
    artifacts = {"summary.json": b"{}\n"}
    publish_bundle(tmp_path, spec, artifacts)
    result = publish_bundle(tmp_path, spec, artifacts)
    assert result.get("validation_mode") == "reconstruction_compared"


def test_missing_stored_artifact_is_an_integrity_failure(tmp_path):
    spec = {"source_id": "synthetic"}
    artifacts = {"summary.json": b"{}\n"}
    result = publish_bundle(tmp_path, spec, artifacts)
    (Path(result["manifest_path"]).parent / "summary.json").unlink()
    try:
        publish_bundle(tmp_path, spec, artifacts)
    except Exception as error:
        assert isinstance(error, BundleIntegrityError)
    else:
        pytest.fail("Missing stored artifact was accepted")


@pytest.mark.parametrize("payload", [None, b"not-json", b"null", b"{}"])
def test_missing_or_malformed_manifest_is_an_integrity_failure(tmp_path, payload):
    spec = {"source_id": "synthetic"}
    artifacts = {"summary.json": b"{}\n"}
    result = publish_bundle(tmp_path, spec, artifacts)
    path = Path(result["manifest_path"])
    if payload is None:
        path.unlink()
    else:
        path.write_bytes(payload)
    try:
        publish_bundle(tmp_path, spec, artifacts)
    except Exception as error:
        assert isinstance(error, BundleIntegrityError)
    else:
        pytest.fail("Invalid manifest was accepted")


def test_corrupted_stored_artifact_is_rejected_without_repair(tmp_path):
    spec = {"source_id": "synthetic"}
    artifacts = {"summary.json": b'{"count":2}\n'}
    result = publish_bundle(tmp_path, spec, artifacts)
    artifact = Path(result["manifest_path"]).parent / "summary.json"
    artifact.write_bytes(b'{"count":3}\n')
    with pytest.raises(BundleIntegrityError):
        publish_bundle(tmp_path, spec, artifacts)
    assert artifact.read_bytes() == b'{"count":3}\n'


def test_different_incoming_content_cannot_reuse_valid_existing_bundle(tmp_path):
    spec = {"source_id": "synthetic"}
    result = publish_bundle(tmp_path, spec, {"summary.json": b'{"count":2}\n'})
    directory = Path(result["manifest_path"]).parent
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in directory.iterdir()}
    with pytest.raises(BundleIntegrityError):
        publish_bundle(tmp_path, spec, {"summary.json": b'{"count":3}\n'})
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in directory.iterdir()} == before


def test_concurrent_identical_publications_verify_the_winning_bundle(tmp_path, monkeypatch):
    barrier = Barrier(2)
    original_rename = Path.rename

    def synchronized_rename(path, target):
        if path.name.startswith(".stage-"):
            barrier.wait(timeout=10)
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", synchronized_rename)
    spec = {"source_id": "synthetic"}
    data = {"summary.json": b"{}\n"}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(publish_bundle, tmp_path, spec, data) for _ in range(2)]
        results = []
        for future in futures:
            try:
                results.append(future.result())
            except OSError:
                results.append(None)
    assert all(result is not None for result in results)
    assert sorted(result["reused"] for result in results) == [False, True]
    assert len({result["profile_id"] for result in results}) == 1
    assert len([p for p in tmp_path.iterdir() if not p.name.startswith(".stage-")]) == 1


def test_unlisted_stored_file_is_rejected_as_inventory_corruption(tmp_path):
    spec = {"source_id": "synthetic"}
    data = {"summary.json": b"{}\n"}
    result = publish_bundle(tmp_path, spec, data)
    directory = Path(result["manifest_path"]).parent
    (directory / "unexpected.json").write_bytes(b"{}\n")
    with pytest.raises(BundleIntegrityError):
        publish_bundle(tmp_path, spec, data)


@pytest.mark.parametrize("metadata", [{}, None, []])
def test_malformed_artifact_metadata_is_an_integrity_failure(tmp_path, metadata):
    spec = {"source_id": "synthetic"}
    data = {"summary.json": b"{}\n"}
    result = publish_bundle(tmp_path, spec, data)
    path = Path(result["manifest_path"])
    manifest = json.loads(path.read_bytes())
    manifest["artifacts"]["summary.json"] = metadata
    path.write_text(json.dumps(manifest))
    try:
        publish_bundle(tmp_path, spec, data)
    except Exception as error:
        assert isinstance(error, BundleIntegrityError)
    else:
        pytest.fail("Malformed artifact metadata was accepted")


@pytest.mark.parametrize("payload", [b'{"value":NaN}\n', b'{"count":1,"count":2}\n'])
def test_noncanonical_json_cannot_be_published_as_canonical(tmp_path, payload):
    with pytest.raises(BundleIntegrityError, match="canonical"):
        publish_bundle(tmp_path, {"source_id": "synthetic"}, {"summary.json": payload})
    assert [p for p in tmp_path.iterdir() if not p.name.startswith(".stage-")] == []


def test_noncanonical_jsonl_records_are_not_published(tmp_path):
    with pytest.raises(BundleIntegrityError, match="canonical"):
        publish_bundle(tmp_path, {"source_id": "synthetic"}, {
            "activities.jsonl": b'{"activity_id":1,"value":NaN}\n',
        })
    assert [p for p in tmp_path.iterdir() if not p.name.startswith(".stage-")] == []


def test_completion_manifest_declares_its_publication_contract(tmp_path):
    result = publish_bundle(tmp_path, {"source_id": "synthetic"}, {"summary.json": b"{}\n"})
    manifest = json.loads(Path(result["manifest_path"]).read_bytes())
    assert manifest.get("completion_contract") == "assaytrace-bundle-v1"


@pytest.mark.parametrize("version", [None, "unknown-v99"])
def test_unsupported_completion_contract_is_rejected_without_rewrite(tmp_path, version):
    spec = {"source_id": "synthetic"}
    artifacts = {"summary.json": b"{}\n"}
    result = publish_bundle(tmp_path, spec, artifacts)
    path = Path(result["manifest_path"])
    manifest = json.loads(path.read_bytes())
    if version is None:
        manifest.pop("completion_contract")
    else:
        manifest["completion_contract"] = version
    path.write_text(json.dumps(manifest))
    before = path.read_bytes(), path.stat().st_mtime_ns
    with pytest.raises(BundleIntegrityError, match="completion contract"):
        publish_bundle(tmp_path, spec, artifacts)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
