from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from collections import Counter, defaultdict
from statistics import median

from assaytrace.chemistry import standardize
from assaytrace.contracts import dedupe_activities
from assaytrace.groups import allocate_groups, build_groups


def molecular_context_profile(context, source_id, chemistry_digest, grouping_digest):
    molecules = [{**row, "source_id": source_id,
                  "identity_id": None, "structure_equivalence_key": None, "scaffold_smiles": None,
                  **standardize(row["source_smiles"], chemistry_digest)}
                 for row in sorted(context["molecules"], key=lambda row: row["molecule_id"])]
    return molecules, build_groups(molecules, grouping_digest)


def profile_evidence(rows, equivalence_groups, scaffold_groups):
    records, repeated = dedupe_activities(rows)
    measured = [{**row, "assay_id": row["source_payload"].get("assay_id"),
                 "document_id": row["source_payload"].get("doc_id"),
                 "potential_duplicate": row["source_payload"].get("potential_duplicate")}
                for row in records if row["measurement_eligible"]]
    allocatable = [row for row in measured if row["allocation_eligible"]]
    identities = {row["identity_id"] for row in allocatable}
    allocations = {}
    contrasts = {}
    for name, mapping in {"equivalence": equivalence_groups, "scaffold": scaffold_groups}.items():
        allocations[name] = allocate_groups({identity: mapping[identity] for identity in sorted(identities)})
        held_out = [identity for identity, partition in allocations[name]["identity_to_partition"].items()
                    if partition != "train"]
        contrasts[name] = contrast_support(allocatable, equivalence_groups, held_out)
    return {"repeat_summary": repeat_summary(measured), "repeat_details": repeat_details(measured),
            "allocation_excluded_measurement_record_count": len(measured) - len(allocatable),
            "allocations": allocations, "contrasts": contrasts}, {"repeated_encounters": repeated}


def contrast_support(rows, identity_to_equivalence_group, held_out_identities):
    retained = defaultdict(list)
    excluded = defaultdict(list)
    unknown = 0
    removed = 0
    held_groups = {identity_to_equivalence_group[identity] for identity in held_out_identities}
    held_records = 0
    reference = set()
    for row in rows:
        flag = row.get("potential_duplicate")
        identity = row["identity_id"]
        if flag not in (0, 1):
            unknown += 1
        if identity_to_equivalence_group[identity] in held_groups:
            held_records += 1
            if identity in held_out_identities and flag == 0:
                reference.add(identity)
            continue
        if flag not in (0, 1):
            continue
        retained[identity].append(Decimal(row["pic50"]))
        if flag == 0:
            excluded[identity].append(Decimal(row["pic50"]))
        else:
            removed += 1
    changed = []
    unchanged = []
    with localcontext() as context:
        context.prec = 34
        context.rounding = ROUND_HALF_EVEN
        for identity in sorted(excluded):
            before, after = median(retained[identity]), median(excluded[identity])
            if before != after:
                changed.append({"identity_id": identity, "retain": format(before, ".12f"),
                                "exclude": format(after, ".12f")})
            else:
                unchanged.append(identity)
    return {"removed_training_identities": sorted(retained.keys() - excluded.keys()),
            "changed_prospective_medians": changed, "unchanged_shared_training_identities": unchanged,
            "removed_training_record_count": removed, "unknown_flag_record_count": unknown,
            "retain_training_identities": sorted(retained), "exclude_training_identities": sorted(excluded),
            "common_reference_identities": sorted(reference), "held_out_group_record_count": held_records,
            "reference_population": "restricted_unflagged_not_ground_truth",
            "aggregation_status": "provisional_what_if_median"}


def conclusions(criteria):
    for name in ("population", "allocation", "curation"):
        criterion = criteria.get(name, {})
        if (criterion.get("status") not in {"supported", "not_supported", "inconclusive"}
                or not isinstance(criterion.get("evidence_refs"), list) or not criterion["evidence_refs"]
                or not isinstance(criterion.get("limitations"), list)
                or not criterion.get("scope") or not criterion.get("next_action")
                or criterion.get("reviewer_confirmation") not in {"assistant_proposed", "human_confirmed"}
                or (criterion["status"] in {"supported", "not_supported"}
                    and criterion.get("reviewer_confirmation") != "human_confirmed")):
            raise ValueError(f"Incomplete or unconfirmed scientific criterion: {name}")
    result = {}
    for conclusion, required in {"prediction": ("population", "allocation"),
                                 "study": ("population", "allocation", "curation")}.items():
        statuses = {criteria[name]["status"] for name in required}
        result[conclusion] = ("not_supported" if "not_supported" in statuses else
                              "inconclusive" if "inconclusive" in statuses else "supported")
    return result


def repeat_details(rows):
    identities = defaultdict(list)
    for row in rows:
        identities[row["identity_id"]].append(row)
    result = []
    for identity_id, records in sorted(identities.items()):
        values = [Decimal(row["pic50"]) for row in records]
        result.append({"identity_id": identity_id, "source_record_count": len(records),
                       "source_assay_count": len({row["assay_id"] for row in records if row["assay_id"] is not None}),
                       "source_document_count": len({row["document_id"] for row in records if row["document_id"] is not None}),
                       "missing_assay_record_count": sum(row["assay_id"] is None for row in records),
                       "missing_document_record_count": sum(row["document_id"] is None for row in records),
                       "distinct_numeric_value_count": len(set(values)),
                       "minimum_pic50": format(min(values), ".12f"),
                       "maximum_pic50": format(max(values), ".12f"),
                       "range_pic50": format(max(values) - min(values), ".12f")})
    return result


def repeat_summary(rows):
    counts = Counter(row["identity_id"] for row in rows if row["identity_id"] is not None)
    return {"source_record_count": len(rows),
            "source_flagged_count": sum(row.get("potential_duplicate") == 1 for row in rows),
            "source_unflagged_count": sum(row.get("potential_duplicate") == 0 for row in rows),
            "source_unknown_flag_count": sum(row.get("potential_duplicate") not in (0, 1) for row in rows),
            "identities_with_multiple_source_records": sum(count > 1 for count in counts.values())}


def molecular_profile(activities, contract_digest):
    molecules = {}
    annotated = []
    for row in activities:
        molecule_id = row["source_payload"]["molregno"]
        if molecule_id not in molecules:
            molecules[molecule_id] = {
                "source_id": row["source_id"], "molecule_id": molecule_id,
                "identity_id": None, "structure_equivalence_key": None, "scaffold_smiles": None,
                **standardize(row["source_smiles"], contract_digest),
            }
        molecule = molecules[molecule_id]
        annotated.append({**row, "identity_id": molecule.get("identity_id"),
                          "structure_reason": molecule.get("reason")})
    counts = {
        "molecular_identity_count": len({row["identity_id"] for row in annotated if row["identity_id"] is not None}),
        "exact_numeric_with_structure_count": sum(row["pic50"] is not None and row["identity_id"] is not None
                                                   for row in annotated),
        "assay_review_status": "not_assessed",
    }
    return annotated, [molecules[key] for key in sorted(molecules)], counts


def pic50(value, unit, relation):
    if not isinstance(relation, str) or relation.strip() != "=":
        raise ValueError("non_exact_relation")
    with localcontext() as context:
        context.prec = 34
        context.rounding = ROUND_HALF_EVEN
        try:
            concentration = Decimal(value)
        except (TypeError, InvalidOperation) as error:
            raise ValueError("missing_or_invalid_value") from error
        if not concentration.is_finite() or concentration <= 0:
            raise ValueError("nonfinite_or_nonpositive_value")
        try:
            molar_exponent = {"M": 0, "mM": 3, "uM": 6, "µM": 6,
                              "μM": 6, "nM": 9, "pM": 12}[unit.strip()]
        except (KeyError, AttributeError) as error:
            raise ValueError("unknown_unit") from error
        return format(Decimal(molar_exponent) - concentration.log10(), ".12f")


def numerical_profile(records, structures, source_id):
    exact_count = 0
    activities = []
    for record in records:
        row = {"source_id": source_id, "activity_id": record["activity_id"],
               "source_payload": record, "pic50": None, "numerical_reason": None,
               "source_smiles": structures.get(record["molregno"])}
        activities.append(row)
        if record["standard_type"] != "IC50":
            row["numerical_reason"] = "wrong_endpoint"
            continue
        try:
            row["pic50"] = pic50(record["standard_value"], record["standard_units"], record["standard_relation"])
        except ValueError as error:
            row["numerical_reason"] = str(error)
            continue
        exact_count += 1
    summary = {"source_record_count": len(records), "exact_numeric_ic50_count": exact_count,
               "source_kind": "synthetic", "source_compatibility": "not_established",
               "study_feasibility": "inconclusive"}
    return activities, summary
