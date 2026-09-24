import pytest
import assaytrace.chemistry as chemistry

from assaytrace.chemistry import standardize


def test_atom_order_does_not_change_measurement_identity():
    first = standardize("CCO", "test-contract")
    second = standardize("OCC", "test-contract")
    assert first is not None
    assert first["parent_smiles"] == second["parent_smiles"] == "CCO"
    assert first["identity_id"] == second["identity_id"]
    assert first["source_smiles"] == "CCO"
    assert second["source_smiles"] == "OCC"


@pytest.mark.parametrize("smiles", ["CCO.c1ccccc1", "CCO.O=S(=O)([O-])[O-]"])
def test_unlisted_components_are_not_silently_discarded(smiles):
    result = standardize(smiles, "test-contract")
    assert result.get("reason") == "ambiguous_components"
    assert result.get("identity_id") is None
    assert result["source_smiles"] == smiles


def test_protonation_is_neutralized_without_removing_permanent_charge():
    salt = standardize("C[NH3+].[Cl-]", "test-contract")
    amine = standardize("CN", "test-contract")
    permanent = standardize("C[N+](C)(C)C", "test-contract")
    assert salt["parent_smiles"] == "CN"
    assert salt["identity_id"] == amine["identity_id"]
    assert permanent["parent_smiles"] == "C[N+](C)(C)C"


@pytest.mark.parametrize("fragment", ["O", "[Cl-]", "[Br-]", "[I-]", "[Li+]",
    "[Na+]", "[K+]", "[Mg+2]", "[Ca+2]"])
def test_only_listed_whole_fragments_are_removed_with_counts(fragment):
    result = standardize(f"CCO.{fragment}.{fragment}", "test-contract")
    assert result.get("parent_smiles") == "CCO"
    assert result["identity_id"] == standardize("CCO", "test-contract")["identity_id"]
    assert result["removed_fragments"] == {fragment: 2}


@pytest.mark.parametrize("smiles, reason", [
    ("O.[Na+]", "no_parent"),
    ("O=S(=O)([O-])[O-]", "no_organic_parent"),
])
def test_identity_requires_one_remaining_carbon_containing_parent(smiles, reason):
    try:
        result = standardize(smiles, "test-contract")
    except IndexError:
        result = {}
    assert result.get("reason") == reason
    assert result.get("identity_id") is None


@pytest.mark.parametrize("smiles, reason", [(None, "missing_structure"),
    ("", "empty_structure"), ("not-a-smiles", "parse_failure"),
    ("C*", "unsupported_atom"), ("[CH3]", "radical"),
    ("C[Si](C)(C)C", "unsupported_element")])
def test_unsupported_structures_are_retained_with_explicit_reasons(smiles, reason):
    try:
        result = standardize(smiles, "test-contract")
    except (TypeError, ValueError):
        result = {}
    assert result.get("reason") == reason
    assert result.get("identity_id") is None
    assert result["source_smiles"] == smiles


def test_stereoisomers_keep_distinct_identities_but_share_equivalence():
    left = standardize("C[C@H](O)C(=O)O", "test-contract")
    right = standardize("C[C@@H](O)C(=O)O", "test-contract")
    assert left["identity_id"] != right["identity_id"]
    assert left.get("structure_equivalence_key") is not None
    assert left["structure_equivalence_key"] == right["structure_equivalence_key"]


def test_tautomers_share_equivalence_without_merging_measurement_identities():
    ketone = standardize("CC(=O)C", "test-contract")
    enol = standardize("C=C(O)C", "test-contract")
    assert ketone["identity_id"] != enol["identity_id"]
    assert ketone["structure_equivalence_key"] == enol["structure_equivalence_key"]


def test_incomplete_enumeration_retains_identity_but_withholds_equivalence(monkeypatch):
    expected_identity = standardize("CC(=O)C", "test-contract")["identity_id"]
    limited = chemistry._tautomer_enumerator()
    limited.SetMaxTautomers(1)
    monkeypatch.setattr(chemistry, "_tautomer_enumerator", lambda: limited)
    result = standardize("CC(=O)C", "test-contract")
    assert result.get("equivalence_reason") == "equivalence_unresolved"
    assert result["identity_id"] == expected_identity
    assert result.get("structure_equivalence_key") is None


def test_scaffolds_use_ring_framework_and_explicit_acyclic_category():
    toluene = standardize("Cc1ccccc1", "test-contract")
    ethylbenzene = standardize("CCc1ccccc1", "test-contract")
    ethanol = standardize("CCO", "test-contract")
    assert toluene.get("scaffold_smiles") == "c1ccccc1"
    assert ethylbenzene["scaffold_smiles"] == "c1ccccc1"
    assert toluene["identity_id"] != ethylbenzene["identity_id"]
    assert ethanol["scaffold_smiles"] == "ACYCLIC"


def test_enhanced_stereo_is_rejected_instead_of_flattened():
    source = "C[C@H](O)C(=O)O |&1:1|"
    result = standardize(source, "test-contract")
    assert result.get("reason") == "unsupported_stereochemistry"
    assert result.get("identity_id") is None
    assert result["source_smiles"] == source


def test_isotopic_hydrogen_and_carbon_remain_distinct_from_unlabelled_parent():
    regular = standardize("CO", "test-contract")
    deuterated = standardize("[2H]OC", "test-contract")
    labelled = standardize("[13CH3]O", "test-contract")
    explicit_h = standardize("[H]OC", "test-contract")
    assert deuterated["parent_smiles"] == "[2H]OC"
    assert labelled["parent_smiles"] == "[13CH3]O"
    assert len({regular["identity_id"], deuterated["identity_id"], labelled["identity_id"]}) == 3
    assert len({regular["structure_equivalence_key"], deuterated["structure_equivalence_key"],
                labelled["structure_equivalence_key"]}) == 3
    assert explicit_h["identity_id"] == regular["identity_id"]


def test_parent_formal_charge_is_reported_after_neutralization():
    amine = standardize("C[NH3+].[Cl-]", "test-contract")
    permanent = standardize("C[N+](C)(C)C", "test-contract")
    assert amine.get("formal_charge") == 0
    assert permanent.get("formal_charge") == 1


def test_non_tetrahedral_stereo_is_outside_the_approved_scope():
    result = standardize("F[P@TB1](Cl)(Br)(I)C", "test-contract")
    assert result.get("reason") == "unsupported_stereochemistry"
    assert result.get("identity_id") is None


def test_enumeration_failure_keeps_measurement_identity_and_scaffold(monkeypatch):
    reference = standardize("Cc1ccccc1", "test-contract")

    class FailingEnumerator:
        def Enumerate(self, molecule):
            raise RuntimeError("injected toolkit enumeration failure")

    monkeypatch.setattr(chemistry, "_tautomer_enumerator", FailingEnumerator)
    try:
        result = standardize("Cc1ccccc1", "test-contract")
    except RuntimeError:
        result = {}
    assert result.get("identity_id") == reference["identity_id"]
    assert result["scaffold_smiles"] == "c1ccccc1"
    assert result["equivalence_reason"] == "equivalence_unresolved"
    assert result.get("structure_equivalence_key") is None


@pytest.mark.parametrize("smiles", ["C[C@H](O)C(=O)O", "F/C=C/F"])
def test_unexplained_stereo_loss_during_normalization_is_not_published_as_identity(monkeypatch, smiles):
    real_factory = chemistry.rdMolStandardize.Uncharger

    class LosingUncharger:
        def __init__(self, **kwargs):
            self.real = real_factory(**kwargs)

        def uncharge(self, molecule):
            result = self.real.uncharge(molecule)
            chemistry.Chem.RemoveStereochemistry(result)
            return result

    monkeypatch.setattr(chemistry.rdMolStandardize, "Uncharger", LosingUncharger)
    result = standardize(smiles, "test-contract")
    assert result.get("reason") == "stereochemistry_lost"
    assert result.get("identity_id") is None


def test_normalization_audit_retains_parent_before_and_after_charge_change():
    result = standardize("C[NH3+].[Cl-]", "test-contract")
    assert result.get("normalization_audit") == {
        "parent_before_charge_smiles": "C[NH3+]",
        "parent_after_charge_smiles": "CN",
        "formal_charge_before": 1,
        "formal_charge_after": 0,
    }
    assert result["removed_fragments"] == {"[Cl-]": 1}
