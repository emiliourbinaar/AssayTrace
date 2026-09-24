from hashlib import sha256
from collections import Counter
import json
from pathlib import Path

from rdkit import Chem, rdBase
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold

from assaytrace.artifacts import canonical_json

_RULES = json.loads((Path(__file__).resolve().parents[2] / "config" / "phase1-chemistry.json").read_text())


def chemistry_contract():
    return {**_RULES, "rdkit_version": rdBase.rdkitVersion}


REMOVABLE_FRAGMENTS = frozenset(
    Chem.MolToSmiles(Chem.MolFromSmiles(value), canonical=True, isomericSmiles=True)
    for value in _RULES["removable_fragments"]
)


def _tautomer_enumerator():
    enumerator = rdMolStandardize.TautomerEnumerator()
    settings = _RULES["tautomer"]
    enumerator.SetMaxTautomers(settings["max_tautomers"])
    enumerator.SetMaxTransforms(settings["max_transforms"])
    enumerator.SetRemoveBondStereo(settings["remove_bond_stereo"])
    enumerator.SetRemoveSp3Stereo(settings["remove_sp3_stereo"])
    enumerator.SetReassignStereo(settings["reassign_stereo"])
    return enumerator


def standardize(smiles, contract_digest):
    if smiles is None:
        return {"source_smiles": smiles, "reason": "missing_structure"}
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        return {"source_smiles": smiles, "reason": "parse_failure"}
    if molecule.GetNumAtoms() == 0:
        return {"source_smiles": smiles, "reason": "empty_structure"}
    if any(atom.GetAtomicNum() == 0 or atom.HasQuery() for atom in molecule.GetAtoms()):
        return {"source_smiles": smiles, "reason": "unsupported_atom"}
    if any(atom.GetNumRadicalElectrons() for atom in molecule.GetAtoms()):
        return {"source_smiles": smiles, "reason": "radical"}
    supported_chirality = {Chem.ChiralType.CHI_UNSPECIFIED,
                          Chem.ChiralType.CHI_TETRAHEDRAL_CW,
                          Chem.ChiralType.CHI_TETRAHEDRAL_CCW}
    if molecule.GetStereoGroups() or any(
        atom.GetChiralTag() not in supported_chirality for atom in molecule.GetAtoms()
    ):
        return {"source_smiles": smiles, "reason": "unsupported_stereochemistry"}
    fragments = Chem.GetMolFrags(molecule, asMols=True, sanitizeFrags=True)
    removed = Counter()
    remaining = []
    for fragment in fragments:
        key = Chem.MolToSmiles(fragment, canonical=True, isomericSmiles=True)
        if key in REMOVABLE_FRAGMENTS:
            removed[key] += 1
        else:
            remaining.append(fragment)
    if len(remaining) > 1:
        return {"source_smiles": smiles, "removed_fragments": dict(removed), "reason": "ambiguous_components"}
    if not remaining:
        return {"source_smiles": smiles, "removed_fragments": dict(removed), "reason": "no_parent"}
    if not any(atom.GetAtomicNum() == 6 for atom in remaining[0].GetAtoms()):
        return {"source_smiles": smiles, "removed_fragments": dict(removed), "reason": "no_organic_parent"}
    if any(atom.GetSymbol() not in _RULES["allowed_elements"]
           for atom in remaining[0].GetAtoms()):
        return {"source_smiles": smiles, "removed_fragments": dict(removed), "reason": "unsupported_element"}
    specified_centers = sum(atom.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
                            for atom in remaining[0].GetAtoms())
    specified_bonds = sum(bond.GetStereo() not in {Chem.BondStereo.STEREONONE, Chem.BondStereo.STEREOANY}
                          for bond in remaining[0].GetBonds())
    parent = rdMolStandardize.Uncharger(**_RULES["uncharger"]).uncharge(Chem.RemoveHs(remaining[0]))
    Chem.SanitizeMol(parent)
    Chem.AssignStereochemistry(parent, cleanIt=True, force=True)
    if (sum(atom.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED
            for atom in parent.GetAtoms()) < specified_centers
            or sum(bond.GetStereo() not in {Chem.BondStereo.STEREONONE, Chem.BondStereo.STEREOANY}
                   for bond in parent.GetBonds()) < specified_bonds):
        return {"source_smiles": smiles, "removed_fragments": dict(removed), "reason": "stereochemistry_lost"}
    parent_smiles = Chem.MolToSmiles(parent, canonical=True, isomericSmiles=True)
    result = {
        "source_smiles": smiles,
        "removed_fragments": dict(removed),
        "parent_smiles": parent_smiles,
        "formal_charge": Chem.GetFormalCharge(parent),
        "normalization_audit": {
            "parent_before_charge_smiles": Chem.MolToSmiles(remaining[0], canonical=True, isomericSmiles=True),
            "parent_after_charge_smiles": parent_smiles,
            "formal_charge_before": Chem.GetFormalCharge(remaining[0]),
            "formal_charge_after": Chem.GetFormalCharge(parent),
        },
        "identity_id": sha256(canonical_json([contract_digest, parent_smiles])).hexdigest(),
    }
    scaffold_parent = Chem.Mol(parent)
    Chem.RemoveStereochemistry(scaffold_parent)
    scaffold = MurckoScaffold.GetScaffoldForMol(scaffold_parent)
    result["scaffold_smiles"] = Chem.MolToSmiles(scaffold, canonical=True, isomericSmiles=True) or "ACYCLIC"
    equivalent = Chem.Mol(parent)
    Chem.RemoveStereochemistry(equivalent)
    enumerator = _tautomer_enumerator()
    try:
        tautomers = enumerator.Enumerate(equivalent)
    except RuntimeError:
        result["equivalence_reason"] = "equivalence_unresolved"
        return result
    if tautomers.status != rdMolStandardize.TautomerEnumeratorStatus.Completed:
        result["equivalence_reason"] = "equivalence_unresolved"
        return result
    equivalent = enumerator.PickCanonical(tautomers)
    equivalence_smiles = Chem.MolToSmiles(equivalent, canonical=True, isomericSmiles=True)
    result["structure_equivalence_key"] = sha256(canonical_json([contract_digest, equivalence_smiles])).hexdigest()
    return result
