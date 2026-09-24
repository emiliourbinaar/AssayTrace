"""Read-only extraction for the explicitly synthetic vertical slice."""

import sqlite3
from contextlib import closing

from assaytrace.source import SourceContractError


def extract_release_slice(source, target_chembl_id, endpoint, *, assay_limit=20, activity_limit=20):
    if any(type(limit) is not int or limit <= 0 for limit in (assay_limit, activity_limit)):
        raise ValueError("Slice limits must be positive integers")
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        required = {
            "version": {"name"},
            "target_dictionary": {"tid", "chembl_id"},
            "assays": {"assay_id", "tid"},
            "activities": {"activity_id", "assay_id", "standard_type"},
        }
        for table, expected in required.items():
            columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
            if missing := expected - columns:
                raise SourceContractError(f"Missing {table} columns: {', '.join(sorted(missing))}")
        if db.execute("SELECT name FROM version WHERE name=?", ("ChEMBL_37",)).fetchone() is None:
            raise SourceContractError("Expected ChEMBL_37 release entry")
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
