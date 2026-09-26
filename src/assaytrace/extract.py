"""Read-only extraction for the explicitly synthetic vertical slice."""

import sqlite3
from contextlib import closing

from assaytrace.source import SourceContractError


def extract_documents(source, document_ids):
    documents = []
    missing = []
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        _validate_release_core(db)
        for document_id in sorted({value for value in document_ids if value is not None}):
            row = db.execute("SELECT * FROM docs WHERE doc_id=?", (document_id,)).fetchone()
            if row is None:
                missing.append(document_id)
            else:
                documents.append(dict(row))
    return {"documents": documents, "missing_document_ids": missing}


def extract_molecule_context(source, molecule_ids):
    candidates = set(molecule_ids)
    pending = list(sorted(candidates))
    molecules = {}
    missing_molecules = set()
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        _validate_release_core(db)
        while pending:
            molecule_id = pending.pop()
            if molecule_id in molecules or molecule_id in missing_molecules:
                continue
            molecule_row = db.execute("SELECT * FROM molecule_dictionary WHERE molregno=?", (molecule_id,)).fetchone()
            if molecule_row is None:
                missing_molecules.add(molecule_id)
                continue
            molecule = dict(molecule_row)
            structure_row = db.execute("SELECT * FROM compound_structures WHERE molregno=?", (molecule_id,)).fetchone()
            structure = dict(structure_row) if structure_row is not None else None
            hierarchy_row = db.execute("SELECT * FROM molecule_hierarchy WHERE molregno=?", (molecule_id,)).fetchone()
            hierarchy = dict(hierarchy_row) if hierarchy_row is not None else None
            claims = [hierarchy["parent_molregno"]] if hierarchy is not None and hierarchy["parent_molregno"] is not None else []
            molecules[molecule_id] = {"molecule_id": molecule_id, "is_candidate": molecule_id in candidates,
                                      "source_smiles": structure["canonical_smiles"] if structure is not None else None,
                                      "source_parent_claims": claims,
                                      "parent_mapping_status": ("absent_mapping" if hierarchy is None else
                                                                "present" if claims else "null_parent"),
                                      "molecule_payload": molecule, "structure_payload": structure,
                                      "hierarchy_payload": hierarchy}
            pending.extend(parent for parent in claims if parent not in molecules)
    return {"molecules": [molecules[key] for key in sorted(molecules)], "missing_molecule_ids": sorted(missing_molecules)}


def _validate_release_core(db):
    required = {"version": {"name"}, "target_dictionary": {"tid", "chembl_id"},
                "assays": {"assay_id", "tid"}, "activities": {"activity_id", "assay_id", "standard_type"}}
    for table, expected in required.items():
        columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
        if missing := expected - columns:
            raise SourceContractError(f"Missing {table} columns: {', '.join(sorted(missing))}")
    if db.execute("SELECT name FROM version WHERE name=?", ("ChEMBL_37",)).fetchone() is None:
        raise SourceContractError("Expected ChEMBL_37 release entry")


def extract_target_candidates(source, target_chembl_id, endpoint):
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        _validate_release_core(db)
        target = dict(db.execute("SELECT * FROM target_dictionary WHERE chembl_id=?", (target_chembl_id,)).fetchone())
        assays = [dict(row) for row in db.execute("SELECT * FROM assays WHERE tid=? ORDER BY assay_id", (target["tid"],))]
        activities = []
        for assay in assays:
            activities.extend(dict(row) for row in db.execute(
                "SELECT * FROM activities INDEXED BY fk_act_assay_id WHERE assay_id=? AND standard_type=?",
                (assay["assay_id"], endpoint)))
        return {"target": target, "assays": assays,
                "activities": sorted(activities, key=lambda row: row["activity_id"])}


def extract_release_slice(source, target_chembl_id, endpoint, *, assay_limit=20, activity_limit=20):
    if any(type(limit) is not int or limit <= 0 for limit in (assay_limit, activity_limit)):
        raise ValueError("Slice limits must be positive integers")
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        _validate_release_core(db)
        target = db.execute("SELECT tid FROM target_dictionary WHERE chembl_id=?", (target_chembl_id,)).fetchone()
        records = [dict(row) for row in db.execute("""
            WITH target_assays AS MATERIALIZED (
                SELECT assay_id FROM assays WHERE tid=? ORDER BY assay_id LIMIT ?
            )
            SELECT a.* FROM target_assays s
            CROSS JOIN activities a INDEXED BY fk_act_assay_id
            WHERE a.assay_id=s.assay_id AND a.standard_type=?
            ORDER BY a.activity_id LIMIT ?
        """, (target["tid"], assay_limit, endpoint, activity_limit))]
        assays = [dict(db.execute("SELECT * FROM assays WHERE assay_id=?", (assay_id,)).fetchone())
                  for assay_id in sorted({row["assay_id"] for row in records})]
        return {"activities": records, "assays": assays}


def extract_synthetic(source):
    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as db:
        if db.execute("SELECT name FROM version").fetchall() != [("assaytrace-synthetic-v1",)]:
            return None
        required = {"activity_id", "standard_type", "standard_value", "standard_units", "standard_relation"}
        columns = {row[1] for row in db.execute("PRAGMA table_info(activities)")}
        if not required <= columns:
            return None
        db.row_factory = sqlite3.Row
        records = [dict(row) for row in db.execute("SELECT * FROM activities ORDER BY activity_id")]
        structures = {row["molregno"]: row["canonical_smiles"]
                      for row in db.execute("SELECT molregno, canonical_smiles FROM compound_structures")}
    return records, structures
