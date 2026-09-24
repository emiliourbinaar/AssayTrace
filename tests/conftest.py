import sqlite3

import pytest


@pytest.fixture
def synthetic_source(tmp_path):
    """Authored fixture schema; it is not a captured ChEMBL response."""
    path = tmp_path / "synthetic.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE version (name TEXT);
            INSERT INTO version VALUES ('assaytrace-synthetic-v1');
            CREATE TABLE activities (
                activity_id INTEGER PRIMARY KEY, assay_id INTEGER, molregno INTEGER,
                standard_type TEXT, standard_value TEXT, standard_units TEXT,
                standard_relation TEXT, potential_duplicate INTEGER);
            CREATE TABLE assays (assay_id INTEGER PRIMARY KEY, tid INTEGER);
            INSERT INTO assays VALUES (1, 220);
            CREATE TABLE compound_structures (molregno INTEGER PRIMARY KEY, canonical_smiles TEXT);
            INSERT INTO compound_structures VALUES (1, 'CCO'), (2, 'c1ccccc1');
            CREATE TABLE target_components (tid INTEGER, component_id INTEGER);
            INSERT INTO target_components VALUES (220, 1), (220, 2);
        """)
        db.executemany("INSERT INTO activities VALUES (?,?,?,?,?,?,?,?)", [
            (1, 1, 1, "IC50", "10", "nM", "=", 0),
            (2, 1, 1, "IC50", "10", "nM", "=", 1),
            (3, 1, 2, "IC50", "100", "nM", "=", 0),
            (4, 1, 1, "Ki", "10", "nM", "=", 0),
            (5, 1, 1, "IC50", "10", "nM", ">", 0),
            (6, 1, 3, "IC50", "10", "nM", "=", None),
        ])
    return path
