"""Authored minimal schema fixtures informed by observed ChEMBL 37 columns.

All values are invented test data, not captured activity records.
"""
import sqlite3

import pytest

from assaytrace.extract import extract_release_slice
from assaytrace.source import SourceContractError


@pytest.fixture
def release_fixture(tmp_path):
    path = tmp_path / "authored-release.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE version (name TEXT PRIMARY KEY);
            INSERT INTO version VALUES ('ChEMBL_37'), ('Other authored version entry');
            CREATE TABLE target_dictionary (tid INTEGER PRIMARY KEY, chembl_id TEXT UNIQUE);
            INSERT INTO target_dictionary VALUES (77, 'CHEMBL_TEST_TARGET'), (88, 'CHEMBL_OTHER');
            CREATE TABLE assays (assay_id INTEGER PRIMARY KEY, tid INTEGER, confidence_score INTEGER);
            INSERT INTO assays VALUES (3, 77, 8), (4, 88, 9), (5, 77, 9);
            CREATE TABLE activities (activity_id INTEGER PRIMARY KEY, assay_id INTEGER,
                standard_type TEXT, standard_value TEXT, potential_duplicate INTEGER, extra_source_field TEXT);
            CREATE INDEX fk_act_assay_id ON activities(assay_id);
            INSERT INTO activities VALUES
                (11, 3, 'IC50', '10', 0, 'preserve me'),
                (12, 3, 'IC50', NULL, 1, 'still preserve'),
                (13, 3, 'Ki', '10', 0, NULL),
                (21, 4, 'IC50', '10', 0, NULL),
                (31, 5, 'IC50', '100', 0, NULL);
        """)
    return path


def test_release_slice_enforces_target_endpoint_and_bounds_without_curation(release_fixture):
    result = extract_release_slice(release_fixture, "CHEMBL_TEST_TARGET", "IC50",
                                   assay_limit=1, activity_limit=20)
    assert result is not None
    assert [row["activity_id"] for row in result["activities"]] == [11, 12]
    assert result["activities"][0]["extra_source_field"] == "preserve me"
    assert result["activities"][1]["standard_value"] is None
    assert result["activities"][1]["potential_duplicate"] == 1
    assert result["assays"] == [{"assay_id": 3, "tid": 77, "confidence_score": 8}]


def test_release_slice_rejects_wrong_release_even_when_tables_match(release_fixture):
    with sqlite3.connect(release_fixture) as db:
        db.execute("UPDATE version SET name='ChEMBL_36' WHERE name='ChEMBL_37'")
    with pytest.raises(SourceContractError, match="release"):
        extract_release_slice(release_fixture, "CHEMBL_TEST_TARGET", "IC50")


@pytest.mark.parametrize("limits", [{"assay_limit": -1}, {"activity_limit": -1},
                                   {"assay_limit": 0}, {"activity_limit": True}])
def test_slice_limits_cannot_disable_the_bounded_read(release_fixture, limits):
    with pytest.raises(ValueError, match="positive integer"):
        extract_release_slice(release_fixture, "CHEMBL_TEST_TARGET", "IC50", **limits)


@pytest.mark.parametrize("table,column", [("version", "name"),
    ("target_dictionary", "chembl_id"), ("assays", "tid"), ("activities", "standard_type")])
def test_missing_adapter_columns_fail_as_source_contract_errors(release_fixture, table, column):
    with sqlite3.connect(release_fixture) as db:
        db.execute(f"ALTER TABLE {table} RENAME COLUMN {column} TO missing_column")
    try:
        extract_release_slice(release_fixture, "CHEMBL_TEST_TARGET", "IC50")
    except Exception as error:
        assert isinstance(error, SourceContractError)
        assert table in str(error)
        assert column in str(error)
    else:
        pytest.fail("Missing source column accepted")
