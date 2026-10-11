"""Composition of independently testable Phase 1 scientific transformations."""
import json
from hashlib import sha256
from pathlib import Path
from datetime import datetime, timezone

from assaytrace.artifacts import canonical_json, read_bundle, publish_bundle, record_run
from assaytrace.chemistry import chemistry_contract
from assaytrace.profile import molecular_context_profile, pic50, profile_evidence
from assaytrace.review import import_reviews, metadata_reasons, record_eligibility
from assaytrace.contracts import dedupe_activities


def processing_specification():
    package = Path(__file__).parent
    workspace = package.parent.parent
    code_inventory = {str(path.relative_to(package)): sha256(path.read_bytes()).hexdigest()
                      for path in sorted(package.glob("*.py"))}
    return {
        "processing_code_sha256": sha256(canonical_json(code_inventory)).hexdigest(),
        "environment_lock_sha256": sha256((workspace / "uv.lock").read_bytes()).hexdigest(),
        "image_definition_sha256": sha256((workspace / "Dockerfile").read_bytes()).hexdigest(),
    }


def publish_candidate_profile(descriptor_path, output, *, synthetic=False):
    started_at = datetime.now(timezone.utc).isoformat()
    descriptor_path, output = Path(descriptor_path), Path(output)
    descriptor = json.loads(descriptor_path.read_bytes())
    paths = {name: descriptor_path.parent / descriptor[name]
             for name in ("candidate", "context", "selection", "reviews")}
    inputs = {name: read_bundle(path) for name, path in paths.items()}
    input_hashes = {name: sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    source_id = inputs["candidate"]["specification"]["source_id"]
    if synthetic:
        if not source_id.startswith("synthetic:"):
            raise ValueError("Synthetic mode requires explicitly synthetic source identity")
    elif source_id != "ChEMBL37:33c203740555f96067710cdfc1c3c55d890660e5908ec5cbf5817492c290d281":
        raise ValueError("Release mode requires the approved pinned ChEMBL37 source identity")
    if any(bundle["specification"].get("source_id") != source_id for bundle in inputs.values()):
        raise ValueError("Input source identities differ")
    candidate_spec = inputs["candidate"]["specification"]
    if candidate_spec.get("target") != "CHEMBL220" or candidate_spec.get("endpoint") != "IC50":
        raise ValueError("Input target or endpoint is outside Phase 1 scope")
    for name in ("context", "selection"):
        if inputs[name]["specification"].get("candidate_manifest_sha256") != input_hashes["candidate"]:
            raise ValueError(f"Candidate provenance link differs: {name}")
    raw = json.loads(inputs["candidate"]["artifacts"]["raw-target.json"])
    context = json.loads(inputs["context"]["artifacts"]["raw-molecules.json"])
    reviews = json.loads(inputs["reviews"]["artifacts"]["reviews.json"])
    selection_bytes = inputs["selection"]["artifacts"]["selection.json"]
    if selection_bytes != inputs["reviews"]["artifacts"]["selection.json"]:
        raise ValueError("Review selection differs from frozen selection")
    queue = json.loads(selection_bytes)
    imported = import_reviews(queue, reviews["decisions"], stop=reviews.get("stop"))
    expected_reviews = {key: value for key, value in imported.items() if key != "audit"}
    if reviews != expected_reviews:
        raise ValueError("Review semantic content differs from its contract")
    if (queue["source_id"] != source_id
            or inputs["selection"]["specification"].get("selection_sha256") != queue["selection_sha256"]
            or inputs["reviews"]["specification"].get("selection_sha256") != queue["selection_sha256"]
            or inputs["reviews"]["specification"].get("semantic_sha256") != reviews["semantic_sha256"]):
        raise ValueError("Review provenance links differ")
    chemistry = chemistry_contract()
    chemistry_digest = sha256(canonical_json(chemistry)).hexdigest()
    grouping = {"revision": "phase1-source-parent-groups-v1", "chemistry_contract_sha256": chemistry_digest}
    grouping_digest = sha256(canonical_json(grouping)).hexdigest()
    specification = {
        "source_id": source_id, "profile_contract": "candidate-reviewed-v1", "assessment": None,
        **processing_specification(),
        "input_manifest_sha256": input_hashes,
        "chemistry_contract": chemistry, "chemistry_contract_sha256": chemistry_digest,
        "grouping_contract": grouping, "grouping_contract_sha256": grouping_digest,
    }
    profile = candidate_profile(raw, context, reviews["decisions"], source_id=source_id,
                                chemistry_digest=chemistry_digest, grouping_digest=grouping_digest)
    summary = {
        "source_kind": "synthetic" if synthetic else "chembl_release_extracts",
        "source_compatibility": "not_established" if synthetic else "stored_extracts_only",
        "source_record_count": len(profile["activities"]),
        "human_confirmed_assay_count": sum(row["confirmation_state"] == "human_confirmed"
                                          for row in reviews["decisions"]),
        "assistant_proposed_assay_count": sum(row["confirmation_state"] == "assistant_proposed"
                                             for row in reviews["decisions"]),
        "unreviewed_selected_assay_count": len(reviews["unreviewed"]),
        "measurement_eligible_record_count": sum(row["measurement_eligible"] for row in profile["activities"]),
        "allocation_eligible_record_count": sum(row["allocation_eligible"] for row in profile["activities"]),
        "scientific_assessment": "not_performed",
    }
    try:
        result = publish_bundle(output / "profiles", specification, {
            "activities.jsonl": b"".join(canonical_json(row) for row in profile["activities"]),
            "molecules.jsonl": b"".join(canonical_json(row) for row in profile["molecules"]),
            "groups.json": canonical_json(profile["groups"]),
            "evidence.json": canonical_json(profile["evidence"]),
            "summary.json": canonical_json(summary),
        })
    except Exception as error:
        record_run(output / "runs", {
            "status": "failed", "profile_id": sha256(canonical_json(specification)).hexdigest(),
            "started_at": started_at, "finished_at": datetime.now(timezone.utc).isoformat(),
            "error_type": type(error).__name__, "error_message": str(error),
        })
        raise
    record_run(output / "runs", {**result, **profile["audit"], "started_at": started_at,
                                  "finished_at": datetime.now(timezone.utc).isoformat()})
    return result


def candidate_profile(raw, context, decisions, *, source_id, chemistry_digest, grouping_digest):
    molecules, groups = molecular_context_profile(context, source_id, chemistry_digest, grouping_digest)
    by_molecule = {row["molecule_id"]: row for row in molecules}
    by_assay = {row["assay_id"]: row for row in raw["assays"]}
    by_review = {row["assay_id"]: row for row in decisions}
    quarantine = {identity: component["reasons"]
                  for component in groups["quarantined_components"]
                  for identity in component["identity_ids"]}
    activities = []
    for payload in raw["activities"]:
        molecule = by_molecule[payload["molregno"]]
        value, numerical_reason = None, None
        if payload.get("standard_type") != "IC50":
            numerical_reason = "wrong_endpoint"
        else:
            try:
                value = pic50(payload.get("standard_value"), payload.get("standard_units"),
                              payload.get("standard_relation"))
            except ValueError as error:
                numerical_reason = str(error)
        eligibility = record_eligibility(
            {**payload, "source_id": source_id}, by_review.get(payload["assay_id"], {}), molecule,
            metadata_issues=metadata_reasons(by_assay[payload["assay_id"]], raw["target"]),
            group_issues=quarantine.get(molecule["identity_id"], []), record_conflicts=[],
        )
        activities.append({"source_id": source_id, "activity_id": payload["activity_id"],
                           "source_payload": payload, "identity_id": molecule["identity_id"],
                           "pic50": value, "numerical_reason": numerical_reason, **eligibility})
    activities, repeated = dedupe_activities(activities)
    activities.sort(key=lambda row: row["activity_id"])
    evidence, audit = profile_evidence(activities, groups["identity_to_equivalence_group"],
                                      groups["identity_to_scaffold_group"])
    audit["repeated_encounters"] = repeated
    return {"activities": activities, "molecules": molecules, "groups": groups,
            "evidence": evidence, "audit": audit}
