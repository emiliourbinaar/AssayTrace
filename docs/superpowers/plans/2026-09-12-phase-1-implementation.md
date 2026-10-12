# AssayTrace Phase 1 Implementation Plan

> **For agentic workers:** After explicit plan approval and the user's execution-mode choice, use `superpowers:subagent-driven-development` or `superpowers:executing-plans`, respectively. Follow `superpowers:test-driven-development` and the applicable TDD Guard instructions. Do not spawn agents before that choice.

**Status:** Approved for inline execution on 2026-09-12 with the user's bounded contract corrections incorporated below. As of 2026-10-11, the reference environment, pinned-source acquisition, bounded adapter check, full candidate extraction, chemistry/grouping, review import and stored-input profile CLI have execution evidence. Scientific review, remaining engineering contracts and phase acceptance are incomplete. Batch 001 remains assistant-proposed at the user's request. The task code blocks below remain requirements, not evidence of completion. See [execution evidence](../../phase1-validation.md) and [interim findings](../../phase1-findings.md).

**Review update, 2026-10-12 UTC:** The user has confirmed assay 2351073 as compatible at assay level and assay 902584 as unresolved. Eight other batch 001 decisions remain assistant-proposed. The preceding dated status describes the earlier checkpoint; see the current batch review record for confirmation provenance.

**Goal:** Produce reproducible, source-backed evidence for the three Phase 1 scientific exit criteria without building the later modeling or orchestration system.

**Architecture:** A small Python package reads a verified release SQLite source and immutable review inputs, profiles records and chemical groups, and publishes a deterministic local JSON bundle. Run/audit metadata is stored separately. A CLI wires the same functions used in tests; no servers or model fitting.

**Tech stack:** Linux reference container, Python 3.12, RDKit (proposed 2026.03.6, matching the documentation consulted), pytest, and the pytest TDD Guard reporter. Standard-library SQLite, decimal, JSON, hashlib, urllib, tarfile, pathlib and unittest.mock suffice otherwise. No pandas, PyArrow or scikit-learn is required in this phase. Package/build versions and image digest are resolved and recorded at the approved environment setup gate; they have not been tested together yet.

**Spec:** [Revised Phase 1 design](../specs/2026-09-11-phase-1-foundation-feasibility-design.md). [Roadmap](../../project-roadmap.md). Read both before executing this plan.

## Global constraints

- Pinned release-backed profiling, one candidate target/endpoint: ChEMBL 37 / CHEMBL220 / P22303 / human AChE / IC50.
- No predictive models, PostgreSQL deployment, Airflow deployment, frontend, or later-phase scaffolding.
- Review cap: 120 distinct assays or six hours active review, whichever first; at most 20 accessible source documents and ten minutes per document inside that total. Earlier evidence-linked blocker stops are permitted.
- Scientific results may be supported, not supported or inconclusive, separately for population, allocation and curation comparison. Synthetic success never certifies source compatibility or scientific feasibility.
- Whole-group separation, explicit missingness/contradictions, original-data preservation, and record lineage are mandatory. Activity/assay/document counts are not counts of independent experiments.
- Preserve existing files including `AGENTS.md`, `.claude` configuration and the historical proposal. No Git initialization or changes to hooks have occurred in planning.
- Any material scientific contract change returns to review before implementing its tests. A toolkit output that disagrees with a justified chemical expectation is investigated, not copied into a new expected value.

## A. Decisions resolved before tests

### A1. Activity records and duplicate semantics

`source_id` identifies release plus archive SHA-256. `activity_key=(source_id,activity_id)` is the sole extraction deduplication key. Compare complete source payloads using canonical field ordering with original values/nulls and types preserved. Transport headers and encounter timestamps are excluded. An identical repeated key is one extracted row plus an encounter count in the run audit. A conflicting payload under the same key raises `SourceConflict` and prevents publication.

Distinct activity keys always remain distinct in `activities.jsonl` and primary summaries, including equal-valued records in the same assay/document. Source `potential_duplicate` flags, explicit source cross-references to a shared observation, and reviewer suspicions are separate annotations with evidence IDs. Do not infer shared observation from equal potency, assay ID, publication, or structure. Do not perform cross-key collapse in Phase 1, even for an annotated shared observation. Report source-record counts and provenance counts, not experimental independence.

Numeric profiling uses standardized IC50 only, explicit `=`, finite positive Decimal values, and exact unit mapping: M→1e9 nM; mM→1e6; uM/µM/μM→1e3; nM→1; pM→1e-3. Trim surrounding whitespace but do not lowercase units. Retain original numeric text. Compute pIC50 with a Decimal context of precision 34 and half-even rounding, serialize to 12 decimal places for logical equality. Reject invalid/unknown units, missing/approximate relations, nonfinite/nonpositive values. Do not substitute pChEMBL or censoring limits. Retain and report source pChEMBL discrepancies; source flags are annotations, with validity restricted to null/Manually validated for the proposed reviewed usable population. Other validity flags are excluded with reasons. Potential-duplicate status is not an exclusion in the broad profiling population because it is the registered contrast. Missing/unknown duplicate flag remains its own category.

### A2. Exact chemistry contract: `phase1-chemistry-v1`

This intentionally limited policy prioritizes traceable relationships over maximal recovery. It may lose compounds; that loss is reported. Use toolkit functions, not handcrafted bond-editing rules. The [RDKit API](https://www.rdkit.org/docs/source/rdkit.Chem.MolStandardize.rdMolStandardize.html) documents the charge and tautomer operations; [MurckoScaffold](https://www.rdkit.org/docs/source/rdkit.Chem.Scaffolds.MurckoScaffold.html) provides scaffold extraction. Documentation is not evidence that our wrappers work; verify them under the locked runtime.

Apply operations in this order:

1. Parse source SMILES using RDKit `MolFromSmiles` with sanitization enabled and preserve the input. Reject parse failure, empty molecule, query/dummy atoms, radicals, or enhanced/unsupported stereochemistry rather than flattening it. Preserve isotopes. Do not infer missing stereochemistry or a racemate from unspecified stereo.
2. Use `GetMolFrags(..., asMols=True, sanitizeFrags=True)` and canonical isomeric SMILES for **whole-fragment exact matching**. Remove only members of this complete list: water `O`; chloride `[Cl-]`; bromide `[Br-]`; iodide `[I-]`; lithium `[Li+]`; sodium `[Na+]`; potassium `[K+]`; magnesium `[Mg+2]`; calcium `[Ca+2]`. Canonicalize these reference fragment literals once with the locked toolkit. No organic solvents or organic counterions are removed in v1; acetate, sulfate, phosphate and unlisted mixtures remain ambiguous rather than being guessed away. No substructure fragment match or largest-fragment selection.
3. Require exactly one remaining connected component, and require that component to contain carbon. No remaining component means `no_parent`; more than one component means `ambiguous_components`, including one organic component accompanied by an unlisted inorganic component. A single carbon-free component is `no_organic_parent`. Do not discard unlisted fragments, including sulfate. A remaining parent with elements outside H,B,C,N,O,F,P,S,Cl,Br,I is `unsupported_element`. Do not disconnect covalently bound metals. Record every removed fragment and count.
4. Normalization consists of RDKit sanitization (valence/aromaticity/conjugation/hybridization), canonical atom-order serialization and ordinary hydrogen suppression with `RemoveHs` while retaining isotopic/stereo-defining hydrogens. Do **not** invoke broad `Cleanup`, `Normalizer`, `Reionizer`, `FragmentParent` or `ChargeParent`; no additional functional-group transform list is implicit. This limited normalization is an explicit design choice, not a claim to implement all ChEMBL standardization rules.
5. Apply `Uncharger(canonicalOrder=True, force=False, protonationOnly=True).uncharge(parent)`, then sanitize and assign stereochemistry. Neutralize removable protonation charges; do not force permanent charge removal or change heavy-atom connectivity to neutralize. Retain unresolved charges. Do not apply pH prediction. A quaternary ammonium must remain charged; primary ammonium chloride and its free amine should reach the same parent identity. Verify stereo-defining information is not lost; unexplained stereo loss is quarantined.
6. Serialize canonical isomeric parent SMILES, preserving isotope and stereochemistry. `identity_id=SHA256(canonical_json([chemistry_contract_digest,parent_smiles]))`. This is the identity for measurement summaries. No tautomer enumeration occurs on this molecule.
7. On a **copy**, remove stereochemistry and enumerate tautomers using `TautomerEnumerator`, locked built-in transform/scoring definitions, `SetMaxTautomers(1000)`, `SetMaxTransforms(1000)`, `SetRemoveBondStereo(True)`, `SetRemoveSp3Stereo(True)`, `SetReassignStereo(False)`. Require `Enumerate(...).status == Completed` and use `PickCanonical(result)` with the toolkit's default scoring. Preserve isotopes. If enumeration reaches a limit/fails, retain measurement identity but exclude it from diagnostic usable counts with `equivalence_unresolved`; never use a partial canonical result as a reliable key.
8. Serialize the canonical tautomer after stereo removal with isomeric serialization enabled to retain isotope labels. Its hashed value is `structure_equivalence_key`. The locked RDKit distribution and parameters identify the exact built-in transforms; changing the dependency lock changes the chemistry contract/profile identity. No custom tautomer transforms are added.
9. On a separate stereo-free copy of the step-6 parent, use `GetScaffoldForMol`; serialize its nonchiral scaffold, preserving isotope labels. Empty scaffolds receive literal `ACYCLIC`. This diagnostic groups all acyclic parents together under scaffold allocation. Do not make the scaffold generic or use tautomer changes to merge summary identities.

**Hand-justified chemical expectations:** `CCO` and `OCC` share identity; methylammonium chloride `C[NH3+].[Cl-]` and methylamine `CN` share neutral parent identity; `C[N+](C)(C)C` stays charged; ethanol plus benzene remains an ambiguous mixture; opposite specified lactic-acid stereoisomers remain distinct identities but share structure-equivalence group; acetone and its enol remain distinct summary identities but share tautomer grouping when enumeration completes; toluene and ethylbenzene have the same benzene Murcko scaffold. Record these chemical rationales in fixture documentation. Expected canonical strings beyond simple cases are not generated using the function under test.

### A3. Source parents, equivalence links and indivisible groups

Extract the ChEMBL hierarchy mappings for candidate molecules and recursively resolve referenced parent rows/structures from the same SQLite release. Parent-only nodes carry no activity/compound count unless actually present in the target population. A missing mapping is not a shared null parent: flag it and use structure-derived grouping. Never merge all missing parents. A dangling parent ID, missing/unparseable referenced structure, multi-parent claim, non-self cycle, or parent whose structure-equivalence key disagrees with the child's is an unresolved/conflicting mapping.

Construct an undirected evidence graph over summary identities and referenced source-parent nodes. Add links for equal structure-equivalence keys and all explicit source-parent claims; retain edge reason/source evidence. Self-parent claims are valid identity links, not cycles. Flag every connected component touching an unresolved/conflicting parent claim as unusable for diagnostic allocation pending review. This conservative quarantine avoids either ignoring a claimed relationship or silently merging incompatible compounds into usable data. Retain its source records and summary identities in the descriptive outputs. Missing *absent* mapping alone is not a conflicting claim and does not quarantine an otherwise valid structural group.

For the remaining usable graph, connected components form `equivalence_group_id`, computed from the sorted member identity IDs plus grouping-contract digest. Transitivity matters: A linked to B and B linked to C means all three stay together, regardless of input order. Parent-only auxiliary nodes do not become observations.

For random-group diagnostics, these equivalence components are indivisible. For scaffold diagnostics, add equality links between usable identities with the same scaffold (including ACYCLIC), then recompute connected components. Equivalence links and scaffold links are a **union**, not alternative rules. This can create large groups; report them rather than break them. Build these links over the entire chemically processable candidate-target universe before filtering to a reviewed subset, then project group IDs onto that subset so filtering cannot sever a known bridge. Components with parent conflicts remain flagged during projection.

Grouping quarantine excludes these components from allocation diagnostics only. Preserve the source records and measurement identities in descriptive outputs, with separate quarantine counts/reasons. A missing/conflicting grouping claim is not evidence that the measurement itself is scientifically invalid. Keep `measurement_eligible` and `allocation_eligible` as separate fields rather than one conflated validity flag.

### A4. Frozen review ordering and eligibility

Coverage list H: up to 60 metadata-screened assays, ordered descending by distinct source molecule IDs on target/endpoint records (potency magnitude, relation, value and manual decisions do not rank them), ties by assay ID. Metadata screening uses B/confidence9/D/human, validated locally. The top-coverage and stratum selections are disjoint.

Remaining assays: stratum `(bao_format or UNKNOWN, year_band)`. Year bands: BEFORE_2000, 2000_2009, 2010_2019, 2020_PLUS, UNKNOWN; null/unparseable values use UNKNOWN. Sort nonempty strata lexically. Within each stratum sort by `SHA256(canonical_json([17,source_id,assay_id]))`, ties by assay ID; round-robin one item per stratum until 60 or exhaustion to form S. Freeze H, S, stratum values and metadata digest. Visit H1,S1,H2,S2,... with remainder appended. No post-review or value-derived strata.

Persist every decision and active-time interval. The review importer validates six-hour/120-assay/20-document/ten-minute-per-document limits and recognizes an explicit earlier decisive-blocker event with evidence. It must not classify a budget stop as scientific failure or automatically fill remaining entries as incompatible. A partially reviewed assay is unresolved until completed. Original selected-but-unvisited entries remain unreviewed. Active-time intervals are run/audit metadata, not scientific identity inputs.

Reviewed usable record = compatible, human-confirmed assay decision AND local metadata eligibility AND finite exact recognized-unit IC50 AND permitted validity flag AND usable structure/group mapping AND no record-level conflicting evidence. A compatible assay does not rescue an invalid record. Preserve machine-proposed versus confirmed decisions and evidence. Phase 1 supports file-based review imports; it does not build an interactive review application.

### A5. Prespecified candidate contrast and exit logic

Register before full profiling: **retain versus exclude records with ChEMBL potential_duplicate=1**, holding other screening constant. This tests treatment of a source warning, not a proven correction of duplicated experiments. Unknown flag values are reported separately and excluded from this candidate comparison; they are not recoded as 0. The broad profile still retains them.

Phase 1 produces descriptive population support only: affected records/identities, retained identities, availability of unflagged reference records, document/assay coverage, and group feasibility. The later evaluation proposal uses identical held-out identities with reviewed usable unflagged exact records under both policies; reference labels would be the median pIC50 of those unflagged records for each held-out identity, fixed once for both policies. Training labels would use the same median rule on each policy's retained records. This is a **candidate future protocol**, not an implemented final label or approved model experiment. Median remains a proposal for later scientific approval; no hierarchical independence weighting is implied.

The common unflagged reference defines a restricted evaluation population, not ground truth. At phase exit, report changes in prospective training identity membership and prospective aggregate labels separately. For the proposed median rule, descriptive what-if summaries may show how many shared training identities would have different median values; these are clearly labeled sensitivity diagnostics, not adopted modeling labels. An identity with only flagged records leaves the exclude-policy population; a shared identity can retain the same prospective median despite record removal. Report unchanged labels and unknown-flag exclusions as well. Record removal alone is insufficient to establish a meaningful modeling contrast. Median aggregation and final evaluation design remain subject to phase-exit review, and the disagreement/aggregation question is not replaced by this feasibility assessment.

Exclude all records of held-out identity/equivalence groups from either proposed training population when computing support counts. Report how many training identities/record sets would change and whether the common reference population covers the intended scope. Report within/between-assay and document context so a nominally nonzero contrast is not automatically called meaningful. Do not interpret concordant/singleton records as ground truth.

A disagreement/aggregation comparison is not automatically feasible merely because there are multiple activity IDs. If repeat/context coverage cannot support it, explicitly recommend narrowing the question to the source-warning contrast (if supported), or report curation-study feasibility as inconclusive/not supported. No silent contrast substitution, threshold selection, or model scoring.

Output three evidence-backed criterion records: `population`, `allocation`, `curation`, each with `status`, `evidence_refs`, `limitations`, `scope`, `reviewer_confirmation`, `next_action`. Status is supported/not_supported/inconclusive. A human interpretation supplies status; software validates completeness and derives summaries. For required criteria, any not_supported means the conclusion is not_supported as scoped; otherwise any inconclusive means inconclusive; otherwise supported. Prediction uses population+allocation; study uses all three. Synthetic fixtures only verify these rules and must label the resulting example conclusion synthetic.

### A6. Diagnostic allocation algorithm

Use seed 17, 70/15/15 targets by identity count, no label stratification. Order indivisible groups by descending usable member count, then SHA-256 of canonical `[17,group_id]`, then group_id. Assign each group to the partition that minimizes the total sum of squared deviations from target identity counts after assignment; ties train, validation, test. Use exact rational targets to avoid platform floating-point tie changes. Run once for equivalence groups and once for scaffold-linked groups. Store desired/actual counts and algorithm revision. Do not reseed/repair using potency labels.

Empty/degenerate partitions trigger diagnostic findings, not a blanket scientific failure. A large connected component, absent label spread, or narrowly covered reviewed population is evidence to interpret. Greedy allocation failure alone does not prove no feasible group assignment exists. Any alternative allocator is a recorded amendment, not an unreported search.

### A7. Content identity, equality and publication

Canonical JSON: UTF-8, LF newline, sorted object keys, compact separators, no JSON NaN/Infinity literals. Numeric source fields preserve their contract types; a nonfinite source SQL floating value is preserved as a tagged object such as `{"source_type":"float","value":"NaN"}` (or `Infinity`/`-Infinity`), distinct from SQL null and from source text. It still fails numerical eligibility. Derived decimals serialize as strings with the declared scale. Arrays representing sets are sorted; scientifically ordered arrays (review queues) retain order. JSONL rows sort by declared primary key. Logical equality compares canonical typed records, not source field ordering or filenames.

`profile_id=SHA256(canonical_json(specification))`, where specification contains source_id and archive hash; extraction/profiling schema versions; hashes of screening, chemistry, grouping, diagnostic split and registered-contrast specifications; frozen review-selection digest; semantic review/record-evidence digest (including confirmation state, excluding reviewer name/timing); criterion-assessment and exit-narrative input digest (explicit null before assessment); processing-code file digest over sorted relative package paths and bytes; and reference environment lock/image digest. Supporting evidence is content-hashed; references to an earlier evidence profile do not refer back to the newly derived profile, preventing cycles. Exclude docs-only changes, tests, run IDs, absolute locations, retrieval times, review times, host name and performance measurements. A source subset fixture uses its own synthetic source_id and never claims ChEMBL release authenticity.

The manifest contains specification, artifact names, row counts, byte hashes, logical hashes and completion contract version, but not its own hash or timestamps. The manifest hash lives in the external run record, avoiding circular hashing. Two distinct artifacts for the same profile must not disagree; a mismatch is failure, not an overwrite or a new random suffix.

| Artifact | Equality/check | Timestamp placement |
|---|---|---|
| Original archive, checksum/license/schema evidence, captured source payload | Original-byte SHA-256 integrity; source identity uses archive hash | Retrieval/access metadata in external acquisition record |
| Immutable extracted target records and parent mappings | Canonical typed logical equality; stored-byte checksum on every reuse | None in deterministic tables |
| Chemistry identities, edges, assignments, summaries, semantic review and selection | Exact canonical logical equality including defined decimal strings; byte integrity for existing files | None |
| Manifest and canonical JSON/JSONL profile outputs | Canonical writer should also reproduce bytes in the same locked environment; logical hashes remain explicit | None |
| Deterministic Markdown evidence tables | Byte equality in locked environment; generated solely from canonical data | None |
| Human exit narrative/evidence decisions | Hash the approved input narrative/evidence as semantic input; changes produce a new profile revision | Author/time attribution in audit record |
| Acquisition/run/review audit logs and TDD evidence | No cross-run equality requirement; append new records; retain integrity individually | All timings, attempt ID, actor, absolute paths, reuse flag and errors |

Stage an entire bundle under a unique sibling staging directory; write and close/fsync artifacts, validate logical hashes/counts, then write manifest **last** within staging. Rename the complete directory atomically into the immutable profile location on the same volume. Readers require the final path and a valid manifest. Never replace a nonempty existing bundle. A competing publication that wins the rename is verified and reused; differing content fails. Staging directories are never read as published outputs.

On rerun, derive the profile specification from immutable inputs, verify the existing manifest, expected artifact inventory, every byte hash, and logical hashes/schema/counts, then return its existing reference. Do not rewrite files or touch their modification times. Append a fresh run record with a new time and `reused=true`. A changed semantic review decision creates another profile; the old profile stays readable.

`publish_bundle` receives newly computed artifacts. If that specification already exists, it must first verify stored integrity and then compare the incoming inventory and each artifact's content with the stored bundle under A7's declared equality contract. Missing/extra artifacts, logical disagreement, or byte disagreement where byte equality is required raise `BundleIntegrityError`, preserving every original file. A concurrent-publication loser performs these same incoming-versus-stored comparisons. A separate deliberate fast-reuse path may verify only stored integrity when recomputation was skipped; record `validation_mode=stored_integrity_only`. Only an actual incoming-output comparison or separate reconstruction can record `validation_mode=reconstruction_compared`. Never describe fast reuse as independent reconstruction evidence.

For full reconstruction validation, compute into a separate validation directory and compare without replacing the original. Interruptions before rename leave only staging; interruption after rename but before run acknowledgment recovers by verifying the published bundle. No cross-filesystem atomicity is claimed. Remove only a specifically verified task-owned stale staging path, never recursively clean the artifact root.

## B. Files and interfaces (to create only after approval)

| File | Responsibility |
|---|---|
| `pyproject.toml`, `uv.lock`, `Dockerfile`, `.gitignore` | Isolated reference/runtime/test setup and lock; no service stack |
| `src/assaytrace/contracts.py` | Typed boundary records, named validation errors and canonical serialization |
| `src/assaytrace/source.py` | Verified archive acquisition/unpack and read-only SQLite source checks |
| `src/assaytrace/extract.py` | Target extraction, activity-key deduplication and parent mapping retrieval |
| `src/assaytrace/chemistry.py` | Ordered A2 operations and chemical audit records |
| `src/assaytrace/groups.py` | A3 links/components and A6 allocation |
| `src/assaytrace/review.py` | Frozen sampling queue, review import, budgets and usable-record intersection |
| `src/assaytrace/profile.py` | Screening, source-record/dispersion/contrast counts and criterion validation |
| `src/assaytrace/artifacts.py` | Specification hashes, bundle verification/publication and separate run records |
| `src/assaytrace/cli.py`, `src/assaytrace/__main__.py` | Real integration wiring; explicit acquisition/profile/review/assessment commands |
| `config/phase1.json`, `config/phase1-chemistry.json` | Versioned A1–A7 choices including fragment literals and candidate contrast |
| `tests/fixtures/README.md`, `tests/conftest.py` | Labeled synthetic SQLite/review cases, expected chemistry relations, fixture builders |
| `tests/unit/`, `tests/integration/`, `tests/source/` | Tests listed in C; public-source checks separately opted in |
| `docs/phase1-operations.md`, `docs/phase1-validation.md` | Executable setup/run instructions and measured test/source evidence after execution |

Use JSON objects at file boundaries; typed dictionaries or dataclasses may wrap them without changing their contract. Boundary schemas are explicit:

- Activity: source_id, activity_id, assay_id, molecule_id, document_id (nullable), complete retained source payload, standard_type/value/units/relation, validity_comment, potential_duplicate, metadata_reasons, record_evidence_refs. Preserve unrecognized source fields in payload.
- Molecule: source_id, molecule_id, source_smiles, source_parent_claims, parent_resolution_status. Chemical result: identity_id/parent_smiles/structure_equivalence_key/scaffold or null on the corresponding failure, formal_charge, status/reasons, transformation audit. Graph inputs use the same `structure_equivalence_key` spelling.
- Assay sampling row: assay_id, molecule_count, bao_format, document_year; **no potency fields** in selector input. Review: assay_id, category, confirmation_state, evidence_refs, record_exceptions. Audit timings live in a different record.
- Group result: identity_to_equivalence_group, identity_to_scaffold_group, evidence_edges, quarantined_components. Assignment: strategy, group_id, identity_id, partition.
- BundleRef: profile_id, manifest_path, manifest_sha256. Run record: attempt_id, profile_id if known, start/end UTC, outcome, reuse flag, acquisition/review/TDD audit refs, error, host/resource metadata.

Public interfaces used by the tests below (all are proposed, not existing):

```python
canonical_bytes(value: object) -> bytes
dedupe_activities(rows: list[dict]) -> tuple[list[dict], int]
pic50(value: str, unit: str, relation: str) -> str  # 12 decimal places
standardize(smiles: str, chemistry: dict) -> dict
build_groups(molecules: list[dict], parent_claims: list[dict], contract: dict) -> dict
allocate(groups: dict[str, list[str]], seed: int = 17) -> list[dict]
review_queue(assays: list[dict], source_id: str, limit_each: int = 60) -> dict
usable(activity: dict, assay_review: dict, chemical_result: dict) -> bool
repeat_summary(rows: list[dict]) -> dict
conclusions(criteria: dict) -> dict
verify_source(sqlite_path: Path, source_spec: dict) -> dict
extract_target(sqlite_path: Path, source_spec: dict) -> dict
publish_bundle(root: Path, specification: dict, artifacts: dict[str, bytes]) -> dict
verify_bundle(path: Path, specification: dict) -> dict
run_profile(source: Path, config: dict, reviews: dict, output: Path) -> dict
main(argv: list[str]) -> int
```

`dedupe_activities` compares each row's source payload; encounter count is excluded from scientific bundle content. `publish_bundle` returns BundleRef fields plus `reused`; run metadata is appended by the caller. Named errors: `SourceConflict`, `SourceContractError`, `MeasurementIneligible`, `BundleIntegrityError`, `ReviewContractError`. Chemistry ineligibility is a result with reasons, not a crashed batch.

## C. Execution tasks and red–green–refactor sequence

Each task includes multiple behaviors. Execute one behavior/test at a time, observe its intended red result, implement only that behavior, rerun, then continue. Do not write all production code before running the listed tests. Missing third-party packages and syntax errors are setup failures, not meaningful red evidence. An importable interface raising `NotImplementedError` is allowed solely to reach a requirement-level red. Record actual red/green commands and reasons; none are claimed in this plan.

### Task 0 — Reference test environment and evidence gate

**Files:** project/test environment files above; preserve existing `.claude` files. **Depends on:** explicit plan approval and execution-mode choice. **Produces:** locked runnable test environment, no scientific conclusion.

- [ ] Inspect Docker/WSL/resources and existing Git/configuration. If a system installation is needed, present that concrete prerequisite through the appropriate permission mechanism; do not replace the reference environment silently.
- [ ] Resolve Python 3.12/RDKit/pytest and reporter in a Linux image; record exact versions, package hashes and image digest in the environment lock before chemistry tests. If proposed RDKit is unavailable/incompatible, stop for a documented contract revision rather than adopting a different chemistry behavior silently.
- [ ] Initialize only the minimal package/test environment and Git if absent. Configure `tdd_guard_project_root` as the absolute container project root `/workspace`; use a mount exposing the reporter's `.claude/tdd-guard/data/test.json` to the host. Inspect whether the active agent actually consumes/enforces that reporter; reporter output alone is not proof of write blocking. Report unavailable enforcement and maintain explicit TDD evidence; do not claim TDD Guard is active without verification.
- [ ] Verify pytest collects and runs a temporary harness smoke test; this checks setup, not application acceptance. Remove the smoke-only test after first meaningful tests exist.

Proposed common test invocation after setup, from PowerShell with the project root mounted into the approved image:

```powershell
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace" -w /workspace assaytrace-phase1:test python -m pytest tests/unit -q
```

Image tag is a convenience name for the recorded digest, not a reproducibility pin. Offline test commands use the already-built locked environment. Public source access is never enabled implicitly by this command.

### Task 1 — Source keys, numerical contract and immutable publication

**Files:** contracts.py, profile.py, artifacts.py; `tests/unit/test_records.py`, `test_measurements.py`; `tests/integration/test_publication.py`. **Interfaces:** A1/A7 and the corresponding B signatures. **Deliverable:** trustworthy small data/artifact boundary before source expansion.

Tests use explicit synthetic records. `source_payload` in these examples is the retained immutable source payload; outer IDs locate it.

```python
def test_equal_values_with_distinct_activity_keys_are_retained():
    a = dict(source_id='synthetic', activity_id=1, source_payload={'value':'10'})
    b = dict(source_id='synthetic', activity_id=2, source_payload={'value':'10'})
    rows, encounters = dedupe_activities([a, b, a])
    assert [r['activity_id'] for r in rows] == [1, 2]
    assert encounters == 1

def test_conflicting_payload_is_not_resolved_by_first_row_wins():
    with pytest.raises(SourceConflict):
        dedupe_activities([
            dict(source_id='synthetic', activity_id=1, source_payload={'value':'10'}),
            dict(source_id='synthetic', activity_id=1, source_payload={'value':'11'})])

@pytest.mark.parametrize('v,u,want', [('1','nM','9.000000000000'),
                                    ('1','uM','6.000000000000')])
def test_pic50_uses_molar_scale(v,u,want):
    assert pic50(v,u,'=') == want
```

- [ ] RED: write/run these tests individually with `python -m pytest tests/unit/test_records.py tests/unit/test_measurements.py -q`; expect loss/conflict or missing conversion behavior, not an unrelated error. Add separate censored, negative/nonfinite, missing unit and flag-category cases from A1.
- [ ] GREEN: implement key/payload validation and decimal conversion as A1, with explicit reasoned failures; do not deduplicate by value.
- [ ] RED: write a publication integration test that publishes one artifact, reruns with the same specification, and asserts identical bytes **and modification times**, `reused=True`, and a new external run record when called through the run wrapper. A corrupt byte must cause `BundleIntegrityError`, never overwrite. First verify canonical logical serialization is invariant to object field order and input row order where declared unordered.

The `profile_spec_fixture` supplies the A7 fields with literal synthetic identifiers, fixed configuration/evidence digests, and null assessment; it does not call production code to construct expected hashes. Example publication assertions:

```python
def test_reuse_verifies_without_rewriting(tmp_path, profile_spec_fixture):
    data = {'summary.json': b'{"source_record_count":2}\n'}
    first = publish_bundle(tmp_path, profile_spec_fixture, data)
    manifest = Path(first['manifest_path'])
    before = (manifest.read_bytes(), manifest.stat().st_mtime_ns)
    second = publish_bundle(tmp_path, profile_spec_fixture, data)
    assert second['reused'] is True
    assert second['profile_id'] == first['profile_id']
    assert (manifest.read_bytes(), manifest.stat().st_mtime_ns) == before
    # Alter a published data byte: retry must detect corruption, not silently repair it.
    artifact = manifest.parent / 'summary.json'
    artifact.write_bytes(b'{"source_record_count":3}\n')
    with pytest.raises(BundleIntegrityError):
        publish_bundle(tmp_path, profile_spec_fixture, data)
    assert artifact.read_bytes() == b'{"source_record_count":3}\n'
```
- [ ] GREEN: implement canonical data, manifest inventory and hashes, staging and atomic final rename as A7. Minimum control flow:

```text
derive final path from specification digest
if final exists: verify stored inventory + every byte/logical hash
                compare newly computed inventory/content under A7; return reused reference
write artifacts in unique sibling stage; close/fsync; validate schemas/counts
write manifest last; rename stage to final without replacement
if concurrent final exists: verify its integrity and compare incoming inventory/content
return reference; append execution metadata outside final
```

- [ ] REFACTOR: separate pure hashing from I/O; run both unit and publication tests; commit only after green. No source compatibility claim yet.

### Task 2 — Minimal end-to-end vertical slice

**Files:** source.py, extract.py, cli.py, __main__.py; `tests/conftest.py`, `tests/fixtures/README.md`, `tests/integration/test_vertical_slice.py`. **Consumes:** Task 1 records/publication. **Produces:** CLI → synthetic SQLite → numeric profile → manifest, including a rerun. Chemistry/review/scaffold fields are explicitly `not_assessed`, not dummy passing implementations.

Define a synthetic schema fixture builder in tests only. Six source rows: IDs 1 and 2 are distinct exact 10 nM IC50 records in assay A for molecule X; ID 3 is exact 100 nM for molecule Y in A; ID 4 is Ki; ID 5 is IC50 with `>`; ID 6 is exact IC50 with a missing structure. A repeated extraction encounter of ID 1 is generated by the extraction test, not a second row in the primary-key source table. Include a second component-link row to catch join multiplication. All assay/source metadata and expected outcomes are labeled synthetic.

```python
def test_cli_publishes_accounted_synthetic_profile(synthetic_source, tmp_path):
    result = main(['profile', '--source', str(synthetic_source),
                   '--synthetic', '--output', str(tmp_path / 'out')])
    assert result == 0
    # read_one_published is a test helper: it reads JSON without computing expectations.
    report = read_one_published(tmp_path / 'out', 'summary.json')
    assert report['source_record_count'] == 6
    assert report['exact_numeric_ic50_count'] == 4
    assert report['source_kind'] == 'synthetic'
    assert report['source_compatibility'] == 'not_established'
    assert report['study_feasibility'] == 'inconclusive'
```

- [ ] RED: implement fixture creation and the CLI test first; run `python -m pytest tests/integration/test_vertical_slice.py -q`. Expected failure is missing pipeline/publication/accounting, not SQLite setup.
- [ ] GREEN: wire real functions, not mocks: verify fixture source contract → extract source rows once → numeric dispositions/counts → publish bundle. Mark unimplemented scientific stages not assessed. CLI synthetic mode cannot assign the official source_id.
- [ ] RED/GREEN: add wrong-version, missing mandatory columns, missing-join retention and repeated-join tests; make local source predicates enforce source contracts. Unknown fields remain in raw payload, while absent mandatory fields prevent full-source claims.
- [ ] RED/GREEN: rerun from the CLI and assert the same manifest/files are reused with a separate new run record; add an invalid-source CLI case returning nonzero and publishing nothing.
- [ ] REFACTOR: keep CLI parsing out of extraction; rerun unit/integration tests and commit. This is the first small vertical slice, not the completed scientific profile.

**Approved next step:** execute Task 6A (acquisition safeguards and bounded actual-source adapter check, defined under Task 6) here, before completing Tasks 3–5. Do not defer source-schema evidence until after all source-dependent functionality is implemented.

### Task 3 — Chemistry and grouping, with independent expectations

**Files:** chemistry.py, groups.py, config/phase1-chemistry.json; `tests/unit/test_chemistry.py`, `test_groups.py`; extend `tests/integration/test_vertical_slice.py`. **Depends on:** A2/A3 approval and Tasks 1–2. **Produces:** summary identities distinct from conservative group IDs.

```python
def test_salt_parent_and_permanent_charge(chemistry_contract):
    salt = standardize('C[NH3+].[Cl-]', chemistry_contract)
    amine = standardize('CN', chemistry_contract)
    assert salt['parent_smiles'] == 'CN'
    assert salt['identity_id'] == amine['identity_id']
    charged = standardize('C[N+](C)(C)C', chemistry_contract)
    assert charged['formal_charge'] == 1

def test_stereoisomers_are_not_merged_for_measurement_summaries(chemistry_contract):
    a = standardize('C[C@H](O)C(=O)O', chemistry_contract)
    b = standardize('C[C@@H](O)C(=O)O', chemistry_contract)
    assert a['identity_id'] != b['identity_id']
    assert a['structure_equivalence_key'] == b['structure_equivalence_key']

def test_two_organic_components_are_not_largest_fragment_selected(chemistry_contract):
    assert standardize('CCO.c1ccccc1', chemistry_contract)['status'] == 'ambiguous_components'

def test_unlisted_inorganic_fragment_is_not_silently_discarded(chemistry_contract):
    assert standardize('CCO.[O-]S(=O)(=O)[O-]', chemistry_contract)['status'] == 'ambiguous_components'
```

- [ ] RED: add/run one A2 chemical-relation test at a time with `python -m pytest tests/unit/test_chemistry.py -q`. Explain its chemical expectation in the fixture README before implementing it. Add isotope retention, tautomer identity/group distinction, neutral/protonated forms, unmapped organic salts, failed/limited enumeration and unsupported structures.
- [ ] GREEN: implement the ordered toolkit operations in A2. The transformations operate on copies when deriving grouping/scaffold outputs; no mutation of the summary parent. Return failure reasons instead of silently changing policy.
- [ ] RED: group fixtures define A/B as equivalent, B/C sharing scaffold, C/D with an explicit parent claim. Assert random equivalence membership and scaffold transitive membership separately; two missing parent mappings never link solely through null; an incompatible parent puts the linked component in quarantine. Add dangling parent, self-parent, non-self cycle and parent-only node cases.
- [ ] GREEN: implement evidence edges, validation, deterministic union-find/connected components and quarantine propagation from A3. Union-find is ordinary graph bookkeeping, not custom chemistry logic.
- [ ] RED/GREEN: integrate chemistry/groups into the six-row CLI fixture. Use X=ethanol and Y=benzene: missing-structure ID 6 remains counted in raw/numeric counts but not usable structure counts; IDs 1/2 remain two records on one identity. No review means no confirmed usable population yet.
- [ ] REFACTOR: isolate toolkit wrapper from grouping; rerun all unit and vertical-slice tests; commit. Do not bless unexpected toolkit output by changing expected relations without review.

### Task 4 — Review ordering, imported evidence and budget recovery

**Files:** review.py; `tests/unit/test_review_selection.py`, `test_review_eligibility.py`; `tests/integration/test_review_resume.py`. **Consumes:** extracted metadata and chemistry results. **Produces:** frozen queue and semantic review inputs separated from audit metadata.

```python
def test_time_limited_queue_includes_both_selection_streams(assay_sampling_fixture):
    q = review_queue(assay_sampling_fixture, 'synthetic', limit_each=2)
    assert q['order'][:4] == [q['high'][0], q['stratified'][0],
                             q['high'][1], q['stratified'][1]]
    assert not (set(q['high']) & set(q['stratified']))

def test_assay_acceptance_cannot_rescue_censored_record(valid_activity, valid_chemistry):
    row = {**valid_activity, 'standard_relation': '>'}
    review = {'category':'compatible', 'confirmation_state':'human_confirmed'}
    assert usable(row, review, valid_chemistry) is False
```

Fixture sampling rows are explicitly authored with unequal coverage, format/year unknowns, and enough assays for both streams. Helpers provide literal rows, not production-computed expectations.

- [ ] RED: run `python -m pytest tests/unit/test_review_selection.py tests/unit/test_review_eligibility.py -q` after each test addition. Add fixed selections invariant to input order; selection unaffected by manual decisions/potency because those fields are excluded from selector input; UNKNOWN strata; remainder behavior.
- [ ] GREEN: implement A4 selections/round-robin/interleave; freeze queue digest and semantic inputs. Validate record exceptions after assay acceptance.
- [ ] RED/GREEN: integration-test an interrupted review import and resume: retain original queue/unvisited suffix; separate time metadata; cap stops remain unreviewed; an evidence-linked early blocker can stop before quota. Invalid budgets/unsupported confirmation state raise `ReviewContractError`; no published profile is overwritten.
- [ ] REFACTOR: separate queue construction, budget audit and semantic review import; run related integration tests and commit. No automated keyword classification is presented as human-reviewed evidence.

### Task 5 — Repeat descriptions, contrast support and criterion decisions

**Files:** profile.py, groups.py; `tests/unit/test_repeat_profile.py`, `test_allocations.py`, `test_exit_criteria.py`; `tests/integration/test_profile_evidence.py`. **Consumes:** source-key-deduplicated records, groups and semantic reviews. **Produces:** descriptive evidence, not final labels/models.

```python
def test_equal_valued_source_records_do_not_disappear():
    rows = [dict(activity_id=i, identity_id='x', assay_id='a', document_id='d',
                 pic50='8.000000000000', potential_duplicate=flag)
            for i, flag in [(1,0),(2,1),(3,0)]]
    s = repeat_summary(rows)
    assert s['source_record_count'] == 3
    assert s['source_flagged_count'] == 1
    assert s['identities_with_multiple_source_records'] == 1

def test_prediction_feasibility_does_not_imply_study_feasibility(criterion_fixture):
    c = criterion_fixture(population='supported', allocation='supported',
                          curation='inconclusive')
    assert conclusions(c) == {'prediction':'supported', 'study':'inconclusive'}
```

`criterion_fixture` is a test helper returning the given statuses plus literal synthetic evidence refs, limitations, scope, reviewer confirmation and next action; it does not infer status. Keep evidence outputs explicitly synthetic.

- [ ] RED/GREEN: test A1 record-count/dispersion contracts, flags versus unknowns and evidence-linked suspected duplication without collapse. Compute source-record summaries without assigning independence or final aggregate labels.
- [ ] RED/GREEN: test A6 whole-group allocation with small hand-derived group sizes, deterministic input-order invariance, fixed tie-breaking and one dominant group; report actual partition counts and empty partitions without automatic scientific rejection.
- [ ] RED/GREEN: test contrast-support populations from A5 with flagged-only, unflagged-only, mixed and unknown-flag identities. Common reference IDs must have eligible reviewed unflagged records; no held-out equivalence member may appear in either hypothetical training population. These are support diagnostics, not a fitted experiment.
- [ ] RED/GREEN: add separate cases for record removal that leaves identity membership and prospective median unchanged, record removal that changes the prospective median, and flagged-only identities that disappear. Report each outcome distinctly. Prospective medians are explicitly provisional descriptive diagnostics, not final labels.
- [ ] RED/GREEN: implement criterion completeness validation and the two derived conclusions, including missing evidence, contradictory supported-without-confirmation cases, budget stop with inconclusive, and affirmative blocker with not_supported.
- [ ] REFACTOR: keep human judgment input separate from mechanically computed evidence. Run `python -m pytest tests/unit/test_repeat_profile.py tests/unit/test_allocations.py tests/unit/test_exit_criteria.py tests/integration/test_profile_evidence.py -q`; commit after green.

### Task 6 — Acquisition, real-source contract and full candidate profile

**Files:** source.py, extract.py, config/phase1.json; `tests/integration/test_acquisition.py`, `tests/source/test_chembl37_contract.py`; docs/phase1-operations.md. **Ordering correction:** Task 6A comprises the acquisition safeguards, resource checks, approved archive acquisition and bounded schema/adapter check below. Execute 6A immediately after Tasks 1–2, before completing Tasks 3–5. Task 6B is full candidate profiling/manual review and still depends on Tasks 3–5. **Produces:** source compatibility evidence separate from synthetic tests and scientific findings.

- [ ] RED: local HTTP fixture server sends truncated bytes, a 503 then success, wrong checksum, and an unsafe tar member. Tests assert no final source or profile appears on failure. Exercise the actual acquisition function with a configurable local URL; do not mock away streaming/hash verification.
- [ ] GREEN: stream to a task-owned `.part`; use 30-second connection/read timeout, at most three attempts for transient connection/429/5xx failures with bounded backoff (1s then 2s in the default policy, Retry-After capped at 60s). Checksum/schema errors fail without blind retries. Restart incomplete downloads rather than introduce range-resume complexity. Verify SHA, enumerate tar members, reject absolute/traversal/symlink/hardlink/device members, then extract only regular files/directories within the verified target. Enforce planned storage bound and fail cleanly on disk exhaustion.
- [ ] REFACTOR: rerun local acquisition and vertical-slice tests before touching the public source. Document the exact behavior instead of adding a general downloader framework.
- [ ] After resource/version checks, acquire `chembl_37_sqlite.tar.gz` from the official release directory and verify the previously recorded SHA-256 `33c203740555f96067710cdfc1c3c55d890660e5908ec5cbf5817492c290d281` against newly retrieved official checksum evidence. A changed checksum requires review. Preserve license/attribution and schema evidence.
- [ ] Inspect the actual pinned SQLite schema read-only before asserting adapter compatibility. Expected source relationships are activities→assays/molecule_dictionary; assays→target_dictionary/docs; compound_structures/molecule_hierarchy→molecule_dictionary; target_components→component_sequences. Validate keys/cardinalities and the release metadata. If names/types differ from the tested source adapter, retain the source-schema finding, write a failing contract test reproducing it from a correctly labeled minimal fixture, revise the adapter under TDD, and document the change. Do not invent captured source payloads or silently accept missing mandatory columns.
- [ ] Execute opt-in `python -m pytest tests/source/test_chembl37_contract.py -q` against the local verified archive database. Validate a bounded row slice against direct SQL counts/IDs and manual source inspection. This source check reads the real schema/records; a synthetic schema with similar names is not sufficient.
- [ ] **Task 6B, after Tasks 3–5:** Run full candidate extraction and metadata/chemical profiling. Freeze the queue before assay review. Conduct bounded review/import, then create a new profile from those immutable semantic decisions. Present evidence-linked assay proposals to the user in batches of up to 10, separating ambiguous cases. Keep them assistant-proposed until the user explicitly confirms the identified decisions; neither silence nor continuation confirms them. Do not train models, silently change target, or select new contrast thresholds.

User-facing operations will distinguish `acquire` (explicit network), `profile` (local input), `review-import` (local ledger) and `assess` (local criterion evidence). Full command arguments, paths and captured output are documented after tested CLI wiring; the interface names and responsibilities are fixed here. No full-source success or feasibility claim is made until the corresponding evidence exists.

### Task 7 — End-to-end failure recovery and final phase evidence

**Files:** artifacts.py and cli.py as needed; `tests/integration/test_failure_recovery.py`, `test_reproducibility.py`; docs/phase1-validation.md. **Consumes:** complete pipeline and real-source evidence. **Produces:** phase exit report and reproducibility record.

- [ ] RED: inject I/O failures before manifest write, before final directory rename, and after successful rename but before run acknowledgment. Use monkeypatch at the filesystem boundary or terminate a subprocess; keep real serialization/extraction/chemistry/publishing. Assert incomplete bundles are not visible and existing complete bytes/mtime remain unchanged. No production-only “test mode” branches.
- [ ] GREEN: implement only missing recovery paths from A7. Retry after lost acknowledgment must verify/reuse the existing bundle. Corruption must fail loudly; never “repair” by overwriting immutable content.
- [ ] RED/GREEN: launch two same-spec publications concurrently on a small fixture; one final valid bundle, both callers either verify/reuse or report an explicit failure, no overwrite. Different content with same specification cannot succeed. Rerun with a changed semantic review category/confirmation state produces a new ID; rerun with changed timestamp/actor alone does not.
- [ ] RED/GREEN: publish a valid payload and then submit a different freshly computed payload under the identical specification while leaving stored files intact. The second call must fail and preserve original bytes/mtime. Test inventory disagreement separately. Fast reuse records integrity-only validation; a reconstruction claim requires actual comparison.
- [ ] REFACTOR: run all required offline unit/integration tests once after relevant changes, then run the complete synthetic CLI path. Record actual red/green commands and results. Do not repeatedly broaden tests without a new change or unresolved issue.
- [ ] Repeat the real candidate profile from identical pinned inputs into a separate validation location. Compare logical source rows, identities, graph edges/groups, selections, allocations, counts and deterministic report tables exactly under their contracts; verify existing bundle byte checksums. Run IDs/timing may differ and stay outside the profile.
- [ ] Assemble three separate evidence layers: (1) synthetic behavior/recovery test outcomes, (2) actual ChEMBL source-contract results, (3) scientific criterion assessments with evidence and limitations. Do not promote success at one layer to the next.
- [ ] Present population/allocation/curation criterion statuses and the two derived conclusions, review-budget usage, unresolved coverage, actual resource measurements and proposed Phase 2 scope. If repeats do not support disagreement/aggregation, name that unsupported question explicitly. Request the phase-exit decision rather than design later phases automatically.

## D. Plan acceptance and outstanding review

All five user revisions map to explicit contracts/tasks: exit decisions A5/Task5/Task7; source-record duplication A1/Task1; interleaved bounded review A4/Task4; exact chemistry/grouping A2–A3/Task3; content/run separation A7/Tasks1 and7. Task2 is the early vertical slice; Tasks3–5 extend its real integration rather than leaving wiring until the end. Task6 establishes source compatibility separately, and Task7 validates recovery and scientific evidence.

Material planning choices to approve are the conservative chemistry/fragment and parent-conflict policy, and the newly explicit **candidate** source-duplicate-warning comparison/reference-population proposal. That contrast does not authorize dropping the original disagreement question without documenting the evidence and a narrowed scope at phase exit. Environment lock hashes and actual source-schema compatibility remain execution-time facts; no invented pins, successful installs, or source validation are implied.

The user explicitly approved **inline execution** and the bounded corrections recorded above. No additional full planning approval is required for these corrections or routine implementation choices within scope. Stop for material scientific/scope changes or required system permissions. Assay decisions require the user's actual evidence-linked confirmation. Execution order is Task 0 → 1 → 2 → 6A → 3 → 4 → 5 → 6B → 7.
