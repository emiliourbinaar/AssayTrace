from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext

from assaytrace.chemistry import standardize


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
    if relation != "=":
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
