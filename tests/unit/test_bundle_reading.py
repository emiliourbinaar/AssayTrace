from pathlib import Path
import json
from hashlib import sha256

import pytest

from assaytrace.artifacts import BundleIntegrityError, canonical_json, publish_bundle, read_bundle


def test_reading_an_immutable_bundle_checks_integrity_without_claiming_reconstruction(tmp_path):
    published = publish_bundle(tmp_path, {"source_id": "synthetic:reader"},
                               {"records.json": canonical_json({"count": 2})})
    path = Path(published["manifest_path"])
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in path.parent.iterdir()}
    result = read_bundle(path)
    assert result is not None
    assert result["specification"] == {"source_id": "synthetic:reader"}
    assert result["artifacts"]["records.json"] == b'{"count":2}\n'
    assert result["validation_mode"] == "stored_integrity_only"
    assert result["profile_id"] == published["profile_id"]
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in path.parent.iterdir()} == before


@pytest.mark.parametrize("name,payload", [("records.json", b'{ "count": 2 }\n'),
                                         ("records.jsonl", b'{ "count": 2 }\n'),
                                         ("records.json", b'not-json')])
def test_reader_enforces_declared_canonical_bytes_even_when_file_hash_matches(tmp_path, name, payload):
    published = publish_bundle(tmp_path, {"source_id": "synthetic:reader"},
                               {name: b'{"count":2}\n'})
    path = Path(published["manifest_path"])
    manifest = json.loads(path.read_bytes())
    (path.parent / name).write_bytes(payload)
    manifest["artifacts"][name].update(size=len(payload), sha256=sha256(payload).hexdigest())
    path.write_bytes(canonical_json(manifest))
    try:
        read_bundle(path)
    except Exception as error:
        assert isinstance(error, BundleIntegrityError), f"Unclassified error: {error!r}"
    else:
        pytest.fail("Noncanonical artifact accepted")


@pytest.mark.parametrize("damage", ["missing_manifest", "invalid_json", "null_manifest",
    "missing_keys", "wrong_contract", "inventory_not_mapping", "metadata_missing",
    "missing_artifact", "extra_artifact", "changed_specification", "unsafe_name"])
def test_reader_classifies_incomplete_or_malformed_bundle_as_integrity_failure(tmp_path, damage):
    published = publish_bundle(tmp_path, {"source_id": "synthetic:reader"},
                               {"records.json": b'{}\n'})
    path = Path(published["manifest_path"])
    manifest = json.loads(path.read_bytes())
    if damage == "missing_manifest":
        path.unlink()
    elif damage == "invalid_json":
        path.write_bytes(b"invalid")
    elif damage == "null_manifest":
        path.write_bytes(b"null")
    elif damage == "missing_keys":
        path.write_bytes(b"{}")
    elif damage == "missing_artifact":
        (path.parent / "records.json").unlink()
    elif damage == "extra_artifact":
        (path.parent / "extra.json").write_bytes(b"{}\n")
    else:
        if damage == "wrong_contract":
            manifest["completion_contract"] = "unsupported"
        elif damage == "inventory_not_mapping":
            manifest["artifacts"] = []
        elif damage == "metadata_missing":
            manifest["artifacts"]["records.json"] = {}
        elif damage == "changed_specification":
            manifest["specification"]["source_id"] = "synthetic:different"
        elif damage == "unsafe_name":
            manifest["artifacts"]["../outside.json"] = manifest["artifacts"].pop("records.json")
        path.write_bytes(canonical_json(manifest))
    try:
        read_bundle(path)
    except Exception as error:
        assert isinstance(error, BundleIntegrityError), f"Unclassified error: {error!r}"
    else:
        pytest.fail("Invalid bundle accepted")


@pytest.mark.parametrize("corruption", ["content", "size", "sha256", "logical_sha256",
                                        "row_count", "equality"])
def test_reader_rejects_corrupt_artifact_without_repair(tmp_path, corruption):
    published = publish_bundle(tmp_path, {"source_id": "synthetic:reader"},
                               {"records.jsonl": b'{"count":2}\n'})
    path = Path(published["manifest_path"])
    if corruption == "content":
        (path.parent / "records.jsonl").write_bytes(b'{"count":3}\n')
    else:
        manifest = json.loads(path.read_bytes())
        manifest["artifacts"]["records.jsonl"][corruption] = "invalid"
        path.write_bytes(canonical_json(manifest))
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in path.parent.iterdir()}
    with pytest.raises(BundleIntegrityError):
        read_bundle(path)
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in path.parent.iterdir()} == before
