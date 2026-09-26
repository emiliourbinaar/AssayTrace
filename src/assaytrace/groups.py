from collections import defaultdict
from hashlib import sha256
from fractions import Fraction

from assaytrace.artifacts import canonical_json


def _components(graph):
    unseen = set(graph)
    while unseen:
        pending = [min(unseen)]
        members = set()
        while pending:
            node = pending.pop()
            if node in members:
                continue
            members.add(node)
            pending.extend(graph[node] - members)
        unseen.difference_update(members)
        yield members


def _node(molecule):
    if molecule.get("identity_id") is None:
        return ("source_molecule", molecule["molecule_id"])
    return ("identity", molecule["identity_id"])


def build_groups(molecules, contract_digest, *, selected_identity_ids=None):
    evidence_edges = []
    by_key = defaultdict(set)
    unresolved = set()
    for molecule in molecules:
        if molecule.get("structure_equivalence_key") is None:
            if molecule.get("identity_id") is not None:
                unresolved.add(molecule["identity_id"])
            continue
        by_key[molecule["structure_equivalence_key"]].add(molecule["identity_id"])
    evidence_graph = {("identity", identity): set() for members in by_key.values() for identity in members}
    for equivalence_key, members in by_key.items():
        anchor = min(members)
        for member in members:
            evidence_graph[("identity", anchor)].add(("identity", member))
            evidence_graph[("identity", member)].add(("identity", anchor))
            if member != anchor:
                evidence_edges.append({"reason": "structure_equivalence", "from_identity": anchor,
                                       "to_identity": member, "structure_equivalence_key": equivalence_key})
    by_molecule = {row["molecule_id"]: row for row in molecules}
    conflicts = defaultdict(set)
    for molecule in molecules:
        source_id = molecule["molecule_id"]
        pending = [parent for parent in molecule.get("source_parent_claims", []) if parent != source_id]
        visited = set()
        while pending:
            current = pending.pop()
            if current == source_id:
                conflicts[_node(molecule)].add("parent_cycle")
                break
            if current in visited:
                continue
            visited.add(current)
            if current in by_molecule:
                pending.extend(parent for parent in by_molecule[current].get("source_parent_claims", [])
                               if parent != current)
        if len(set(molecule.get("source_parent_claims", []))) > 1:
            conflicts[_node(molecule)].add("multiple_parent_claims")
        for parent_id in molecule.get("source_parent_claims", []):
            evidence_edges.append({"reason": "source_parent_claim", "source_id": molecule.get("source_id"),
                                   "source_molecule_id": molecule["molecule_id"], "parent_molecule_id": parent_id})
            parent = by_molecule.get(parent_id)
            child_identity = _node(molecule)
            evidence_graph.setdefault(child_identity, set())
            if parent is None:
                parent_identity = ("source_molecule", parent_id)
                evidence_graph.setdefault(parent_identity, set())
                evidence_graph[child_identity].add(parent_identity)
                evidence_graph[parent_identity].add(child_identity)
                conflicts[child_identity].add("dangling_parent")
                continue
            if parent.get("structure_equivalence_key") is None:
                parent_identity = _node(parent)
                evidence_graph.setdefault(parent_identity, set())
                evidence_graph[child_identity].add(parent_identity)
                evidence_graph[parent_identity].add(child_identity)
                conflicts[child_identity].add("parent_structure_unresolved")
                continue
            parent_identity = _node(parent)
            evidence_graph[child_identity].add(parent_identity)
            evidence_graph[parent_identity].add(child_identity)
            if molecule.get("structure_equivalence_key") is None:
                conflicts[child_identity].add("parent_equivalence_unresolved")
            elif molecule["structure_equivalence_key"] != parent["structure_equivalence_key"]:
                conflicts[child_identity].add("parent_equivalence_conflict")
    assignments = {}
    quarantine = []
    usable_components = []
    for nodes in _components(evidence_graph):
        members = {value for kind, value in nodes if kind == "identity"}
        reasons = sorted({reason for node in nodes for reason in conflicts[node]})
        if reasons:
            quarantine.append({"identity_ids": sorted(members), "reasons": reasons})
            continue
        usable_components.append(members)
        group_id = sha256(canonical_json([contract_digest, sorted(members)])).hexdigest()
        assignments.update(dict.fromkeys(members, group_id))
    scaffold_buckets = defaultdict(set)
    for molecule in molecules:
        if molecule["identity_id"] in assignments:
            scaffold_buckets[molecule["scaffold_smiles"]].add(molecule["identity_id"])
    graph = {identity: set() for identity in assignments}
    for scaffold, members in scaffold_buckets.items():
        anchor = min(members)
        for member in members - {anchor}:
            evidence_edges.append({"reason": "scaffold", "from_identity": anchor,
                                   "to_identity": member, "scaffold_smiles": scaffold})
    for members in [*usable_components, *scaffold_buckets.values()]:
        anchor = min(members)
        for member in members:
            graph[anchor].add(member)
            graph[member].add(anchor)
    scaffold_assignments = {}
    for members in _components(graph):
        group_id = sha256(canonical_json([contract_digest, sorted(members)])).hexdigest()
        scaffold_assignments.update(dict.fromkeys(members, group_id))
    candidates = {row["identity_id"] for row in molecules if row.get("is_candidate", True)}
    if selected_identity_ids is not None:
        candidates.intersection_update(selected_identity_ids)
    assignments = {identity: group for identity, group in assignments.items() if identity in candidates}
    scaffold_assignments = {identity: group for identity, group in scaffold_assignments.items() if identity in candidates}
    return {"identity_to_equivalence_group": assignments,
            "identity_to_scaffold_group": scaffold_assignments,
            "quarantined_components": quarantine,
            "evidence_edges": sorted(evidence_edges, key=canonical_json),
            "unresolved_identities": sorted(unresolved)}
def allocate_groups(identity_to_group):
    groups = defaultdict(list)
    for identity, group in identity_to_group.items():
        groups[group].append(identity)
    targets = {"train": Fraction(7, 10) * len(identity_to_group),
               "validation": Fraction(3, 20) * len(identity_to_group),
               "test": Fraction(3, 20) * len(identity_to_group)}
    counts = dict.fromkeys(targets, 0)
    assignment = {}
    for group in sorted(groups, key=lambda key: (-len(groups[key]),
                                                 sha256(canonical_json([17, key])).hexdigest(), key)):
        size = len(groups[group])
        partition = min(targets, key=lambda candidate: sum(
            (counts[name] + (size if name == candidate else 0) - targets[name]) ** 2
            for name in targets))
        assignment[group] = partition
        counts[partition] += size
    return {"group_to_partition": assignment, "counts": counts,
            "empty_partitions": [name for name, count in counts.items() if count == 0],
            "target_counts": {name: str(value) for name, value in targets.items()},
            "identity_to_partition": {identity: assignment[group] for identity, group in sorted(identity_to_group.items())}}
