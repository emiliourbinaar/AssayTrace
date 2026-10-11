# Phase 1 local profile artifacts

This dictionary describes `candidate-reviewed-v1`, a feasibility profile rather
than a final modeling dataset. All files are UTF-8 canonical JSON or JSONL, with
sorted object keys, compact separators and LF terminators. The manifest declares
byte SHA-256 and size for each artifact, plus logical hash, JSON document/JSONL
row count and `canonical_bytes` equality. JSON document count is not a scientific
record count.

| Artifact | Grain / keys | Interpretation |
|---|---|---|
| `manifest.json` | One completed profile; directory key is SHA-256 of canonical specification | Specification pins source identity, four input manifests, processing code, dependency lock, image definition and chemistry/grouping contracts. Publication is atomic; run times and paths are not scientific identity. |
| `activities.jsonl` | One distinct `(source_id, activity_id)` | Full source activity payload, measurement identity, calculated pIC50 or numerical exclusion reason, measurement/allocation eligibility and separate reason lists. Equal-valued source IDs are retained. Conflicting payloads for the same release-qualified key fail. |
| `molecules.jsonl` | One source molecule ID, including recursive auxiliary parents | Original source molecule/structure/hierarchy payloads, source-parent claims, candidate flag, standardized measurement identity and conservative equivalence/scaffold fields. Auxiliary parents do not add activity observations. |
| `groups.json` | One full-context graph result | Candidate identity-to-equivalence/scaffold mappings, evidence edges, unresolved identities and quarantined components. Graph construction precedes reviewed-population projection. These mappings do not establish assay eligibility. |
| `evidence.json` | One diagnostic result for eligible reviewed records | Source-record repeat counts and dispersion, allocation-excluded measurement count, group-preserving allocations and candidate source-warning contrast support. No automatic feasibility verdict. |
| `summary.json` | One accounting summary | All source activity count, eligible measurement/allocation counts, confirmed/proposed decision counts, unreviewed selected assay count and evidence-state labels. |
| `runs/<uuid>.json` | One successfully acknowledged execution | Bundle reference/hash, reuse/comparison state and repeated encounter count. Separate from the immutable profile. Current `started_at` is recorded at acknowledgment time, not a measured execution start; timing/error audit improvements remain pending. |

Measurement identities preserve the approved stereochemical/isotopic distinctions;
equivalence and scaffold groups are conservative leakage-control groups. An
`allocation_quarantine:*` reason identifies grouping uncertainty, not evidence
that a measurement is scientifically invalid. Missing or unconfirmed assay review
prevents measurement eligibility even when numerical and chemistry checks pass.

`repeat_summary` counts source records and identities with multiple records.
`repeat_details` reports source assay/document counts, missing links, distinct
numeric values and pIC50 minimum/maximum/range. None proves independent experiments.
The retained original payload preserves source warning flags and source pChEMBL;
dedicated pChEMBL-discrepancy diagnostics are not yet implemented.

Both allocation diagnostics use seed 17 and whole groups with target identity
fractions 70/15/15; actual counts and empty partitions are explicit. Contrast
support treats validation and test identities as held out of training. The common
unflagged reference population is restricted, not ground truth. Unknown flags are
counted separately. Prospective medians are provisional what-if diagnostics, not
approved labels or evidence that record removal improves prediction.

`source_kind=chembl_release_extracts` and
`source_compatibility=stored_extracts_only` describe this command's input scope.
The separate source-contract test establishes its own bounded adapter evidence.
`scientific_assessment=not_performed` explicitly defers the three scientific exit
criteria. No model evaluation or final modeling dataset is produced here.
