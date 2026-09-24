import argparse
from hashlib import sha256
from pathlib import Path

from assaytrace.artifacts import canonical_json, publish_bundle, record_run
from assaytrace.extract import extract_synthetic
from assaytrace.profile import numerical_profile, molecular_profile
from assaytrace.chemistry import chemistry_contract
from assaytrace.groups import build_groups


def main(argv=None):
    parser = argparse.ArgumentParser(prog="assaytrace")
    commands = parser.add_subparsers(dest="command", required=True)
    profile = commands.add_parser("profile")
    profile.add_argument("--source", type=Path, required=True)
    profile.add_argument("--synthetic", action="store_true", required=True)
    profile.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    extracted = extract_synthetic(args.source)
    if extracted is None:
        return 1
    records, structures = extracted
    source_id = "synthetic:" + sha256(args.source.read_bytes()).hexdigest()
    activities, summary = numerical_profile(records, structures, source_id)
    package = Path(__file__).parent
    workspace = package.parent.parent
    code_inventory = {str(path.relative_to(package)): sha256(path.read_bytes()).hexdigest()
                      for path in sorted(package.glob("*.py"))}
    specification = {
        "source_id": source_id, "profile_contract": "synthetic-numeric-v1", "assessment": None,
        "processing_code_sha256": sha256(canonical_json(code_inventory)).hexdigest(),
        "environment_lock_sha256": sha256((workspace / "uv.lock").read_bytes()).hexdigest(),
        "image_definition_sha256": sha256((workspace / "Dockerfile").read_bytes()).hexdigest(),
        "chemistry_contract": chemistry_contract(),
        "chemistry_contract_sha256": sha256(canonical_json(chemistry_contract())).hexdigest(),
    }
    activities, molecules, chemical_counts = molecular_profile(activities, specification["chemistry_contract_sha256"])
    summary.update(chemical_counts)
    grouping_contract = {
        "revision": "synthetic-structure-groups-v1",
        "chemistry_contract_sha256": specification["chemistry_contract_sha256"],
        "source_parent_assessment": "not_assessed",
    }
    specification["grouping_contract"] = grouping_contract
    specification["grouping_contract_sha256"] = sha256(canonical_json(grouping_contract)).hexdigest()
    groups = build_groups(molecules, specification["grouping_contract_sha256"])
    groups.update(grouping_scope="synthetic_structure_only", source_parent_assessment="not_assessed",
                  assay_review_status="not_assessed")
    result = publish_bundle(args.output / "profiles", specification, {
        "summary.json": canonical_json(summary),
        "activities.jsonl": b"".join(canonical_json(row) for row in activities),
        "molecules.jsonl": b"".join(canonical_json(row) for row in molecules),
        "groups.json": canonical_json(groups),
    })
    record_run(args.output / "runs", result)
    return 0
