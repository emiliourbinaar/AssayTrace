import json
import math
import os
from hashlib import sha256
from pathlib import Path
from tempfile import mkdtemp
from datetime import datetime, timezone
from uuid import uuid4


class BundleIntegrityError(ValueError):
    pass


def record_run(root, result):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{uuid4().hex}.json"
    record = {**result, "started_at": datetime.now(timezone.utc).isoformat(),
              "manifest_sha256": sha256(Path(result["manifest_path"]).read_bytes()).hexdigest()}
    with path.open("xb") as stream:
        stream.write(canonical_json(record))
    return str(path)


def _source_values(value):
    if isinstance(value, float) and not math.isfinite(value):
        label = "NaN" if math.isnan(value) else ("Infinity" if value > 0 else "-Infinity")
        return {"source_type": "float", "value": label}
    if isinstance(value, dict):
        return {key: _source_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_source_values(item) for item in value]
    return value


def canonical_json(value):
    return (json.dumps(_source_values(value), sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _write_synced(path, payload):
    path.write_bytes(payload)
    with path.open("rb") as stream:
        os.fsync(stream.fileno())


def publish_bundle(root, specification, artifacts):
    for name in artifacts:
        if not name or "/" in name or "\\" in name or name in {".", "..", "manifest.json"}:
            raise ValueError("invalid_artifact_name")
    profile_id = sha256(canonical_json(specification)).hexdigest()
    directory = Path(root) / profile_id
    if directory.exists():
        try:
            manifest = json.loads((directory / "manifest.json").read_bytes())
        except (OSError, ValueError) as error:
            raise BundleIntegrityError("Missing or malformed manifest") from error
        if not isinstance(manifest, dict) or not {"specification", "artifacts"} <= manifest.keys():
            raise BundleIntegrityError("Malformed manifest structure")
        if manifest.get("completion_contract") != "assaytrace-bundle-v1":
            raise BundleIntegrityError("Unsupported completion contract")
        if canonical_json(manifest["specification"]) != canonical_json(specification):
            raise BundleIntegrityError("Stored specification differs")
        if set(manifest["artifacts"]) != set(artifacts):
            raise BundleIntegrityError("Incoming artifact inventory differs")
        if {path.name for path in directory.iterdir()} != set(artifacts) | {"manifest.json"}:
            raise BundleIntegrityError("Stored artifact inventory differs")
        for name, metadata in manifest["artifacts"].items():
            required = {"size", "sha256"}
            if name.endswith((".jsonl", ".json")):
                required |= {"row_count", "logical_sha256", "equality"}
            if not isinstance(metadata, dict) or not required <= metadata.keys():
                raise BundleIntegrityError(f"Malformed artifact metadata: {name}")
            try:
                stored = (directory / name).read_bytes()
            except FileNotFoundError as error:
                raise BundleIntegrityError(f"Stored artifact missing: {name}") from error
            if len(stored) != metadata["size"] or sha256(stored).hexdigest() != metadata["sha256"]:
                raise BundleIntegrityError(f"Stored artifact corrupt: {name}")
            if name.endswith((".jsonl", ".json")):
                rows = ([json.loads(line) for line in stored.splitlines()]
                        if name.endswith(".jsonl") else [json.loads(stored)])
                logical = b"".join(canonical_json(row) for row in rows)
                if (metadata["row_count"] != len(rows)
                        or metadata["logical_sha256"] != sha256(logical).hexdigest()
                        or metadata["equality"] != "canonical_bytes"):
                    raise BundleIntegrityError(f"Stored logical metadata corrupt: {name}")
            if stored != artifacts[name]:
                raise BundleIntegrityError(f"Incoming artifact differs: {name}")
        return {"profile_id": profile_id,
                "manifest_path": str(directory / "manifest.json"), "reused": True,
                "validation_mode": "reconstruction_compared"}
    Path(root).mkdir(parents=True, exist_ok=True)
    stage = Path(mkdtemp(prefix=".stage-", dir=root))
    inventory = {}
    for name, payload in artifacts.items():
        _write_synced(stage / name, payload)
        inventory[name] = {"size": len(payload), "sha256": sha256(payload).hexdigest()}
        if name.endswith(".jsonl"):
            rows = [json.loads(line) for line in payload.splitlines()]
            logical = b"".join(canonical_json(row) for row in rows)
            if logical != payload:
                raise BundleIntegrityError(f"Noncanonical JSONL artifact: {name}; canonical bytes required")
            inventory[name].update(row_count=len(rows), logical_sha256=sha256(logical).hexdigest(),
                                   equality="canonical_bytes")
        elif name.endswith(".json"):
            logical = canonical_json(json.loads(payload))
            if logical != payload:
                raise BundleIntegrityError(f"Noncanonical JSON artifact: {name}; canonical bytes required")
            inventory[name].update(row_count=1, logical_sha256=sha256(logical).hexdigest(),
                                   equality="canonical_bytes")
    manifest_path = stage / "manifest.json"
    _write_synced(manifest_path, canonical_json({"completion_contract": "assaytrace-bundle-v1",
                                                "specification": specification,
                                                "artifacts": inventory}))
    try:
        stage.rename(directory)
    except OSError:
        if not directory.exists():
            raise
        return publish_bundle(root, specification, artifacts)
    return {"profile_id": profile_id, "manifest_path": str(directory / "manifest.json"), "reused": False}
