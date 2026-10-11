from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from itertools import zip_longest
from pathlib import Path

from assaytrace.artifacts import canonical_json, publish_bundle, record_run
from assaytrace.profile import pic50


class ReviewContractError(ValueError):
    pass


def assay_sampling_rows(raw, documents):
    by_document = {row["doc_id"]: row for row in documents}
    molecules = defaultdict(set)
    for activity in raw["activities"]:
        if activity["standard_type"] == "IC50":
            molecules[activity["assay_id"]].add(activity["molregno"])
    return [{"assay_id": assay["assay_id"], "molecule_count": len(molecules[assay["assay_id"]]),
             "bao_format": assay.get("bao_format"),
             "document_year": by_document.get(assay.get("doc_id"), {}).get("year")}
            for assay in sorted(raw["assays"], key=lambda row: row["assay_id"])
            if molecules[assay["assay_id"]] and not metadata_reasons(assay, raw["target"])]


def review_budget(intervals):
    total = 0
    documents = defaultdict(float)
    spans = []
    for interval in intervals:
        start = datetime.fromisoformat(interval["start"])
        end = datetime.fromisoformat(interval["end"])
        if start.tzinfo is None or end.tzinfo is None or end < start:
            raise ReviewContractError("Active intervals require timezone-aware, ordered timestamps")
        spans.append((start, end))
        seconds = (end - start).total_seconds()
        total += seconds
        if interval.get("document_id") is not None:
            documents[str(interval["document_id"])] += seconds
    spans.sort()
    if any(right[0] < left[1] for left, right in zip(spans, spans[1:])):
        raise ReviewContractError("Active intervals overlap")
    if total > 21600 or len(documents) > 20 or any(seconds > 600 for seconds in documents.values()):
        raise ReviewContractError("Review budget exceeded")
    return {"active_seconds": total, "document_seconds": dict(sorted(documents.items())),
            "document_count": len(documents), "time_cap_reached": total == 21600}


def publish_reviews(root, queue, decisions, *, intervals=(), stop=None):
    started_at = datetime.now(timezone.utc).isoformat()
    budget = review_budget(intervals)
    imported = import_reviews(queue, decisions, stop=stop)
    content = {key: value for key, value in imported.items() if key != "audit"}
    specification = {"review_contract": "review-import-v1", "source_id": queue["source_id"],
                     "selection_sha256": queue["selection_sha256"],
                     "semantic_sha256": imported["semantic_sha256"]}
    result = publish_bundle(Path(root) / "reviews", specification,
                            {"selection.json": canonical_json(queue), "reviews.json": canonical_json(content)})
    run_path = record_run(Path(root) / "runs", {**result, "review_audit": imported["audit"],
                                               "budget": budget, "active_intervals": list(intervals),
                                               "started_at": started_at,
                                               "finished_at": datetime.now(timezone.utc).isoformat()})
    return {**result, "run_record": run_path}


def import_reviews(queue, decisions, *, stop=None):
    if stop is not None:
        if (stop.get("reason") != "decisive_blocker" or not stop.get("evidence_refs")
                or not stop.get("explanation")
                or stop.get("confirmation_state") not in {"assistant_proposed", "human_confirmed"}):
            raise ReviewContractError("Decisive blocker requires evidence, explanation and explicit confirmation state")
    selection = {key: value for key, value in queue.items() if key != "selection_sha256"}
    if sha256(canonical_json(selection)).hexdigest() != queue.get("selection_sha256"):
        raise ReviewContractError("Frozen selection digest mismatch")
    for decision in decisions:
        if decision.get("source_id") != queue["source_id"] or decision.get("assay_id") not in queue["order"]:
            raise ReviewContractError("Review does not belong to the frozen source/selection")
        if decision.get("confirmation_state") not in {"assistant_proposed", "human_confirmed"}:
            raise ReviewContractError("Unsupported confirmation state")
        if decision.get("category") not in {"compatible", "incompatible", "unresolved"}:
            raise ReviewContractError("Unsupported review category")
        if not isinstance(decision.get("evidence_refs"), list) or not decision["evidence_refs"]:
            raise ReviewContractError("Evidence references must be a nonempty list")
        if any(not isinstance(ref, str) or not ref.strip() for ref in decision["evidence_refs"]):
            raise ReviewContractError("Evidence references must be nonempty strings")
        if not isinstance(decision.get("record_exceptions"), list):
            raise ReviewContractError("Record exceptions must be a list")
        for exception in decision["record_exceptions"]:
            if (not isinstance(exception, dict) or type(exception.get("activity_id")) is not int
                    or not isinstance(exception.get("reason"), str) or not exception["reason"].strip()
                    or not isinstance(exception.get("evidence_refs"), list) or not exception["evidence_refs"]
                    or any(not isinstance(ref, str) or not ref.strip() for ref in exception["evidence_refs"])):
                raise ReviewContractError("Record exceptions require activity_id, reason and evidence references")
    by_assay = {decision["assay_id"]: decision for decision in decisions}
    if len(by_assay) != len(decisions):
        raise ReviewContractError("Duplicate assay decision in review snapshot")
    semantic = []
    audit = []
    for assay_id in queue["order"]:
        if assay_id not in by_assay:
            continue
        decision = by_assay[assay_id]
        semantic.append({key: decision[key] for key in (
            "source_id", "assay_id", "category", "confirmation_state", "evidence_refs", "record_exceptions")})
        semantic[-1].update({key: decision[key] for key in ("doc_id", "rationale", "missing_evidence") if key in decision})
        audit.append({"assay_id": assay_id, "reviewer": decision.get("reviewer"),
                      "reviewed_at": decision.get("reviewed_at")})
    content = {"selection_sha256": queue["selection_sha256"], "decisions": semantic,
               "unreviewed": [assay_id for assay_id in queue["order"] if assay_id not in by_assay],
               "stop": stop}
    return {**content, "semantic_sha256": sha256(canonical_json(content)).hexdigest(), "audit": audit}


def record_eligibility(activity, review, chemistry, *, metadata_issues, group_issues, record_conflicts):
    reasons = reviewed_record_reasons(
        activity, review, chemistry, metadata_issues=metadata_issues,
        group_issues=group_issues, record_conflicts=record_conflicts,
    )
    measurement_reasons = [reason for reason in reasons
                           if not reason.startswith("allocation_quarantine:")
                           and reason != "equivalence_unresolved"]
    return {"measurement_eligible": not measurement_reasons,
            "allocation_eligible": not reasons,
            "measurement_reasons": measurement_reasons, "allocation_reasons": reasons}


def reviewed_record_reasons(activity, review, chemistry, *, metadata_issues, group_issues, record_conflicts):
    reasons = [f"metadata:{reason}" for reason in metadata_issues]
    reasons.extend(f"allocation_quarantine:{reason}" for reason in group_issues)
    reasons.extend(f"record_conflict:{reason}" for reason in record_conflicts)
    if review.get("source_id") == activity.get("source_id") and review.get("assay_id") == activity.get("assay_id"):
        reasons.extend(f"record_conflict:{exception['reason']}" for exception in review.get("record_exceptions", [])
                       if exception["activity_id"] == activity.get("activity_id"))
    if review.get("category") != "compatible":
        reasons.append("assay_not_compatible")
    if review.get("confirmation_state") != "human_confirmed":
        reasons.append("review_not_human_confirmed")
    if not review.get("evidence_refs"):
        reasons.append("review_evidence_missing")
    if review.get("assay_id") is None or activity.get("assay_id") is None:
        reasons.append("review_assay_link_missing")
    elif review.get("assay_id") != activity.get("assay_id"):
        reasons.append("review_assay_link_mismatch")
    if review.get("source_id") is None or activity.get("source_id") is None:
        reasons.append("review_source_missing")
    elif review.get("source_id") != activity.get("source_id"):
        reasons.append("review_source_mismatch")
    if activity.get("standard_type") != "IC50":
        reasons.append("wrong_endpoint")
    else:
        try:
            pic50(activity.get("standard_value"), activity.get("standard_units"), activity.get("standard_relation"))
        except ValueError as error:
            reasons.append(f"numerical:{error}")
    if activity.get("data_validity_comment") not in (None, "Manually validated"):
        reasons.append("validity_flag_not_permitted")
    if chemistry.get("identity_id") is None:
        reasons.append("structure_unresolved")
    if chemistry.get("structure_equivalence_key") is None:
        reasons.append("equivalence_unresolved")
    return reasons


def metadata_reasons(assay, target):
    reasons = []
    for field, expected in {"assay_type": "B", "confidence_score": 9,
                            "relationship_type": "D", "assay_organism": "Homo sapiens"}.items():
        value = assay.get(field)
        if value is None or value == "":
            reasons.append(f"{field}_missing")
        elif value != expected:
            reasons.append(f"{field}_mismatch")
    for field, (expected, label) in {
        "chembl_id": ("CHEMBL220", "target_identity"),
        "target_type": ("SINGLE PROTEIN", "target_type"),
        "organism": ("Homo sapiens", "target_organism"),
    }.items():
        value = target.get(field)
        if value is None or value == "":
            reasons.append(f"{label}_missing")
        elif value != expected:
            reasons.append(f"{label}_mismatch")
    if assay.get("tid") is None or target.get("tid") is None:
        reasons.append("target_link_missing")
    elif assay["tid"] != target["tid"]:
        reasons.append("target_link_mismatch")
    return reasons


def _year_band(year):
    try:
        year = int(str(year))
    except ValueError:
        return "UNKNOWN"
    if year < 2000:
        return "BEFORE_2000"
    if year < 2010:
        return "2000_2009"
    if year < 2020:
        return "2010_2019"
    return "2020_PLUS"


def review_queue(rows, source_id, *, limit_each=60):
    if type(limit_each) is not int or not 1 <= limit_each <= 60:
        raise ReviewContractError("Review stream limit must be an integer from 1 to 60")
    if len({row["assay_id"] for row in rows}) != len(rows):
        raise ReviewContractError("Duplicate assay in sampling metadata")
    ranked = sorted(rows, key=lambda row: (-row["molecule_count"], row["assay_id"]))
    high = [row["assay_id"] for row in ranked[:limit_each]]
    strata = defaultdict(list)
    for row in ranked[limit_each:]:
        stratum = (row.get("bao_format") or "UNKNOWN", _year_band(row.get("document_year")))
        strata[stratum].append(row["assay_id"])
    for members in strata.values():
        members.sort(key=lambda assay_id: (sha256(canonical_json([17, source_id, assay_id])).hexdigest(), assay_id))
    stratified = []
    offset = 0
    while len(stratified) < limit_each:
        round_members = [strata[key][offset] for key in sorted(strata) if offset < len(strata[key])]
        if not round_members:
            break
        stratified.extend(round_members[:limit_each - len(stratified)])
        offset += 1
    order = [item for pair in zip_longest(high, stratified) for item in pair if item is not None]
    frozen_strata = [{"assay_id": row["assay_id"], "bao_format": row.get("bao_format") or "UNKNOWN",
                      "year_band": _year_band(row.get("document_year"))}
                     for row in sorted(rows, key=lambda row: row["assay_id"])]
    fields = ("assay_id", "molecule_count", "bao_format", "document_year")
    metadata = [{key: row.get(key) for key in fields} for row in sorted(rows, key=lambda row: row["assay_id"])]
    queue = {"revision": "review-selection-v1", "source_id": source_id, "seed": 17,
             "limit_each": limit_each, "high": high, "stratified": stratified,
             "order": order, "strata": frozen_strata,
             "metadata_sha256": sha256(canonical_json(metadata)).hexdigest()}
    queue["selection_sha256"] = sha256(canonical_json(queue)).hexdigest()
    return queue
