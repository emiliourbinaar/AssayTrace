"""Authored minimal schema fixtures informed by observed ChEMBL 37 columns.

All values are invented test data, not captured activity records.
"""
import sqlite3

import pytest

from assaytrace.extract import extract_release_slice, extract_target_candidates, extract_molecule_context, extract_documents
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


def test_full_candidate_extraction_preserves_all_target_endpoint_records_before_curation(release_fixture):
    result = extract_target_candidates(release_fixture, "CHEMBL_TEST_TARGET", "IC50")
    assert result is not None
    assert [row["activity_id"] for row in result["activities"]] == [11, 12, 31]
    assert [row["assay_id"] for row in result["assays"]] == [3, 5]
    assert result["activities"][0]["extra_source_field"] == "preserve me"
    assert result["activities"][1]["standard_value"] is None
    assert result["target"] == {"tid": 77, "chembl_id": "CHEMBL_TEST_TARGET"}


def test_full_extraction_rejects_an_unpinned_release(release_fixture):
    with sqlite3.connect(release_fixture) as db:
        db.execute("UPDATE version SET name='ChEMBL_36' WHERE name='ChEMBL_37'")
    with pytest.raises(SourceContractError, match="release"):
        extract_target_candidates(release_fixture, "CHEMBL_TEST_TARGET", "IC50")


@pytest.mark.parametrize("table,column", [("version", "name"), ("target_dictionary", "chembl_id"),
                                        ("assays", "tid"), ("activities", "standard_type")])
def test_full_extraction_identifies_missing_source_columns(release_fixture, table, column):
    with sqlite3.connect(release_fixture) as db:
        db.execute(f"ALTER TABLE {table} RENAME COLUMN {column} TO absent_column")
    try:
        extract_target_candidates(release_fixture, "CHEMBL_TEST_TARGET", "IC50")
    except Exception as error:
        assert isinstance(error, SourceContractError)
        assert table in str(error) and column in str(error)
    else:
        pytest.fail("Missing source column accepted")


def test_molecular_context_recursively_preserves_parent_rows_without_counting_them_as_candidates(release_fixture):
    with sqlite3.connect(release_fixture) as db:
        db.executescript("""
            CREATE TABLE molecule_dictionary (molregno INTEGER PRIMARY KEY, chembl_id TEXT);
            CREATE TABLE compound_structures (molregno INTEGER PRIMARY KEY, canonical_smiles TEXT);
            CREATE TABLE molecule_hierarchy (molregno INTEGER PRIMARY KEY, parent_molregno INTEGER);
            INSERT INTO molecule_dictionary VALUES (1, 'SYNTHETIC1'), (2, 'SYNTHETIC2'), (3, 'SYNTHETIC3');
            INSERT INTO compound_structures VALUES (1, 'CCO.[Cl-]'), (2, 'CCO'), (3, 'c1ccccc1');
            INSERT INTO molecule_hierarchy VALUES (1, 2), (2, 2);
        """)
    result = extract_molecule_context(release_fixture, [1, 3])
    assert result is not None
    molecules = {row["molecule_id"]: row for row in result["molecules"]}
    assert set(molecules) == {1, 2, 3}
    assert molecules[1]["source_parent_claims"] == [2]
    assert molecules[2]["source_parent_claims"] == [2]
    assert molecules[2]["is_candidate"] is False
    assert molecules[3]["is_candidate"] is True
    assert molecules[3]["parent_mapping_status"] == "absent_mapping"
    assert molecules[3]["source_parent_claims"] == []
    assert molecules[1]["source_smiles"] == "CCO.[Cl-]"
    assert molecules[1]["hierarchy_payload"] == {"molregno": 1, "parent_molregno": 2}


def test_missing_parent_context_remains_explicit_instead_of_crashing_or_inventing_links(release_fixture):
    with sqlite3.connect(release_fixture) as db:
        db.executescript("""
            CREATE TABLE molecule_dictionary (molregno INTEGER PRIMARY KEY);
            CREATE TABLE compound_structures (molregno INTEGER PRIMARY KEY, canonical_smiles TEXT);
            CREATE TABLE molecule_hierarchy (molregno INTEGER PRIMARY KEY, parent_molregno INTEGER);
            INSERT INTO molecule_dictionary VALUES (1), (2), (3), (4);
            INSERT INTO compound_structures VALUES (1, 'CCO'), (3, 'CCN'), (4, 'CCC');
            INSERT INTO molecule_hierarchy VALUES (1, 2), (2, 2), (3, 999), (4, NULL);
        """)
    try:
        result = extract_molecule_context(release_fixture, [1, 3, 4])
    except Exception as error:
        pytest.fail(f"Missing source context must be represented explicitly: {error}")
    assert result["missing_molecule_ids"] == [999]
    molecules = {row["molecule_id"]: row for row in result["molecules"]}
    assert molecules[2]["source_smiles"] is None
    assert molecules[2]["structure_payload"] is None
    assert molecules[3]["source_parent_claims"] == [999]
    assert molecules[4]["source_parent_claims"] == []
    assert molecules[4]["parent_mapping_status"] == "null_parent"


@pytest.mark.parametrize("extractor", [extract_molecule_context, extract_documents])
def test_context_cannot_be_read_from_an_unpinned_release(release_fixture, extractor):
    with sqlite3.connect(release_fixture) as db:
        db.execute("UPDATE version SET name='ChEMBL_36' WHERE name='ChEMBL_37'")
    with pytest.raises(SourceContractError, match="release"):
        extractor(release_fixture, [])


def test_document_context_preserves_unknown_years_and_reports_missing_references(release_fixture):
    with sqlite3.connect(release_fixture) as db:
        db.executescript("""
            CREATE TABLE docs (doc_id INTEGER PRIMARY KEY, year INTEGER, doi TEXT);
            INSERT INTO docs VALUES (1, 2001, 'synthetic:doi1'), (2, NULL, NULL);
        """)
    result = extract_documents(release_fixture, [2, 1, 2, None, 99])
    assert result == {"documents": [{"doc_id": 1, "year": 2001, "doi": "synthetic:doi1"},
                                    {"doc_id": 2, "year": None, "doi": None}],
                      "missing_document_ids": [99]}


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
