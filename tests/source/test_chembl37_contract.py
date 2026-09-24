"""Opt-in compatibility check, separate from synthetic tests and feasibility.

Requires the local database extracted from the checksum-verified approved archive.
The environment variable selects that existing database; this test never downloads.
"""
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from assaytrace.extract import extract_release_slice


def test_real_release_slice_matches_captured_ids_and_direct_primary_key_reads():
    location = os.environ.get("ASSAYTRACE_CHEMBL37_SQLITE")
    if not location:
        pytest.skip("Opt in with ASSAYTRACE_CHEMBL37_SQLITE; routine tests remain offline synthetic")
    path = Path(location)
    assert path.is_file()
    result = extract_release_slice(path, "CHEMBL220", "IC50", assay_limit=20, activity_limit=20)
    # Observed from a bounded direct source inspection, not invented fixture IDs.
    expected_ids = [72128, 72135, 73143, 73147, 74190, 74194, 75262, 77570,
                    78619, 79743, 82059, 82066, 84152, 85117, 87149, 88189,
                    88195, 89159, 90065, 91122]
    assert [row["activity_id"] for row in result["activities"]] == expected_ids
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        target = dict(db.execute("SELECT * FROM target_dictionary WHERE chembl_id=?", ("CHEMBL220",)).fetchone())
        assert (target["target_type"], target["organism"], target["tax_id"]) == (
            "SINGLE PROTEIN", "Homo sapiens", 9606)
        components = db.execute("""
            SELECT cs.accession, tc.homologue FROM target_components tc
            JOIN component_sequences cs ON cs.component_id=tc.component_id WHERE tc.tid=?
        """, (target["tid"],)).fetchall()
        assert [tuple(row) for row in components] == [("P22303", 0)]
        direct = [dict(db.execute("SELECT * FROM activities WHERE activity_id=?", (key,)).fetchone())
                  for key in expected_ids]
        assert result["activities"] == direct
        for assay in result["assays"]:
            assert assay["tid"] == target["tid"]
            assert assay == dict(db.execute("SELECT * FROM assays WHERE assay_id=?", (assay["assay_id"],)).fetchone())
    assert len({row["activity_id"] for row in result["activities"]}) == 20
    assert all(row["standard_type"] == "IC50" for row in result["activities"])
