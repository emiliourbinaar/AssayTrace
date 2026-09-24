# Phase 1 design: foundation and scientific feasibility

**Status:** Approved for inline execution on 2026-09-12 with the [implementation plan](../plans/2026-09-12-phase-1-implementation.md). The bounded corrections below supersede earlier planning-only approval wording. No further planning approval is required absent a material scientific/scope change. Required system permissions and human assay confirmation remain explicit.

### Approved execution clarifications

- After removing only the listed fragments, require exactly one remaining connected component, containing carbon. An organic component plus unlisted inorganic material, including sulfate, remains ambiguous.
- Source-parent grouping quarantine concerns allocation diagnostics, not measurement validity. Preserve source records and measurement identities in descriptive outputs with separate quarantine counts/reasons.
- Assess retain-versus-exclude potential_duplicate=1 only as a candidate source-warning sensitivity analysis. Unknown flags stay separate. The unflagged reference is a restricted population, not ground truth. Report prospective training identity-membership and aggregate-label changes, not only removed-record counts. Clearly labeled what-if median summaries may inform feasibility; median aggregation/final evaluation remain for phase-exit review, and the original disagreement question is not silently replaced.
- Publication receiving newly computed artifacts under an existing specification verifies both stored integrity and incoming inventory/content agreement. A difference fails without modifying the original. Deliberate non-recomputing reuse verifies integrity only and cannot be claimed as independent reconstruction.
- After the first vertical slice and tested acquisition safeguards, move the bounded actual-source schema/adapter check earlier. Resource-permitting archive acquisition is approved; full scientific profiling and manual review remain later.
- Follow explicit TDD even if automated TDD Guard enforcement is unavailable. Bring evidence-linked assay proposals in batches of up to 10, separating ambiguous cases. Never mark assistant proposals human-confirmed without the user's explicit review.

Current execution evidence is recorded in [Phase 1 validation](../../phase1-validation.md).

**Parent:** [Project roadmap](../../project-roadmap.md). **Evidence:** [Initial proposal](../plans/2026-09-11-assaytrace.md), section 1. This is a design specification, not a task-by-task implementation plan.

## 1. Objective and completion meaning

Establish whether the proposed target and endpoint can support an interpretable curation-and-splitting study, using a reproducible, independently testable profiling path. Resolve source access, resource feasibility, chemical identity, scaffold structure, repeat-measurement availability, and a bounded assessment of assay compatibility before building the complete ETL/modeling system.

Phase 1 can finish with **supported**, **not supported**, or **inconclusive under the agreed review budget**. Completing its engineering deliverables does not certify scientific feasibility. Only supported evidence justifies proposing Phase 2 with the selected scope; an inconclusive or negative result requires an explicit decision on further investigation or a changed scope.

The exit report must assess three criteria separately: (A) a coherent reviewed prediction population, (B) practically usable whole-group train/validation/test allocation, and (C) at least one meaningful prespecified curation comparison with an interpretable evaluation population. Each criterion has its own status, evidence references, limitations and next action. Prediction feasibility depends on A and B; feasibility of the proposed curation-and-splitting study additionally depends on C. No overall discretionary verdict may replace these assessments. A review-budget expiry is not evidence of scientific failure.

No predictive models are fitted in this phase. No later-phase component is required to count standardized compounds or scaffolds.

## 2. Prior evidence versus current assumptions

The earlier session recorded ChEMBL 37 API status and archive metadata, broad activity totals for AChE IC50, EGFR IC50, and D2 Ki, and small samples exposing assay-description/organism inconsistencies. It also recorded ignored nested activity-endpoint filters, supporting explicit local joins and validation rather than trust in request parameters alone. These are historical observations; raw API response fixtures were not preserved.

AChE IC50 remains a **candidate**, not a confirmed feasible dataset. The earlier record does not establish final eligible counts, distinct standardized compounds, scaffold diversity, suitable repeat measurements, or a manageable complete assay-review workload. Historical Docker/Python/disk observations are not a current readiness assessment. This documentation revision does not repeat network feasibility checks or assert new source facts.

The original values of 1,000/800 compounds, one-log-unit disagreement, hierarchical medians, exact model settings, and resource budgets are not inherited as approved requirements.

## 3. Scope and alternatives

### Recommended: release-backed local profiling

After the design and implementation plan are approved, verify the environment, obtain the official pinned release archive, extract only the target-related records into immutable local profiling artifacts, and execute a minimal tested chemistry/profile workflow. Use no PostgreSQL server, Airflow deployment, or model training in Phase 1. A repeatable CLI-style entry point is enough; exact modules and commands belong in the later implementation plan.

| Approach | Benefit | Cost/limit | Recommendation |
|---|---|---|---|
| Official archived SQLite release, local target extraction | Repeatable source identity and explicit SQL joins; complete target-level profiling | One full archive transfer and sufficient temporary disk space | Preferred, subject to resource checks and implementation approval |
| Small live-API snapshot | Low initial transfer and useful bounded reconnaissance | Snapshot coverage and release consistency limit conclusions; cannot by itself establish archive-backed reproducibility | Contingency for additional reconnaissance only; label feasibility incomplete |
| Full ChEMBL PostgreSQL restoration | SQL access on the eventual database technology | Adds server restore and storage work before target suitability is known | Defer unless archive-reading constraints justify a revised design |

A full archive download is proposed **during approved Phase 1 execution**, not during current planning. Failure of the preferred access route produces a documented blocker and an alternative proposal; it does not authorize an unrecorded source substitution.

### Included

- Host/container capability assessment and an isolated, reproducible Python/RDKit profiling environment.
- Source checksum/version validation; original-data preservation; target-local extraction with explicit joins.
- Minimum measurement validation, molecular identities/equivalence groups, scaffold profiling, and repeat-measurement summaries.
- Bounded manual assay review, coverage reporting, scientific feasibility judgment, and a proposed Phase 2 scope.
- Offline synthetic tests, a small real-source contract check when explicitly enabled, and repeatable publication of profiling artifacts.

### Excluded

Full application schema, PostgreSQL loading, Airflow DAGs, final modeling datasets, final curation policies or labels, hyperparameter/model experiments, production deployment, frontend work, exhaustive literature review, and implementation/design documents for later phases.

## 4. Environment and source contracts

Assess Docker Desktop/WSL availability, architecture, allocatable RAM/CPU, available storage on the actual artifact volume, and expected archive/unpack space. Recommend Linux containers as the reference environment because they align with later orchestration. Select and lock compatible dependencies in the implementation plan; existing global Python should not be modified. Resolve whether TDD Guard can operate in the chosen development setup and document any enforcement limitation instead of claiming it is active without evidence.

If Docker is unavailable, document the installation requirement and options before execution. A native isolated Python feasibility environment is an alternative requiring a documented design change; it is not automatically treated as validation of the later container environment. No installation is authorized by this draft alone.

Use the proposed ChEMBL 37 archive at a release-specific URL and the official checksum. Before acquiring large files, verify available space and the published transfer size; report the estimate and its uncertainty. Recheck checksum metadata at execution time and compare with the historical evidence. Unexpected changes fail closed for review rather than silently replacing the expected hash.

Preserve untouched source bytes, source URL, release, retrieval UTC timestamp, checksum evidence, measured byte count, schema/version metadata, and associated license/attribution. No successful download is claimed until the full hash matches. Local artifacts carry content identity, provenance, schema/contract version, and the profiling environment and rule revision.

Logical extraction grain is one source activity per release-qualified activity ID. Retain source assay, molecule, target/component, document, and structure identifiers and relevant metadata. Extract all activities for the candidate target so wrong-endpoint and missing-data exclusions can be counted. One-to-many component joins must not inflate activity counts. Missing joined data becomes an explicit disposition rather than disappearing through an inner join.

The archive and target subset remain immutable. Persist complete profile bundles through temporary files, validation, and same-filesystem rename; publish the manifest last as the consumer-visible completion marker. A rerun of the same input/rules/environment reuses or verifies identical outputs; different content under the same identity is an error. Interrupted work cannot replace the last complete bundle. No database transaction protocol is required before a database exists.

Separate deterministic content from execution metadata. Profile content identity covers source archive identity, canonical extraction/screening/chemistry/grouping/review-selection/diagnostic-allocation contracts, semantic review decisions and supporting-evidence hashes, processing-code identity, and reference-environment lock. It excludes retrieval/run/review timestamps, elapsed time, host paths, attempt IDs, reviewer names and log messages. Those belong in append-only run/audit records linked to the profile. Review category, confirmation state and evidence changes are scientific changes and produce a new profile; timing changes alone do not. The plan specifies byte versus logical equality for every artifact class and canonical serialization. An existing immutable bundle is verified and reused, never rewritten with a new timestamp under its old identity.

## 5. Minimum scientific profiling design

### Measurement and assay screening

For the initial AChE candidate, profile human target CHEMBL220/P22303 and IC50 separately from all other endpoints. A metadata-screened candidate record has direct single-protein assignment, binding assay type, confidence 9, direct relationship, and human assay organism. Enforce these predicates after joining assay records locally. Missing or contradictory metadata is reported, not inferred from the human target label.

For numerical profiling, require explicit exact relation, a finite positive value, and a recognized molar concentration unit; convert to nM and pIC50 without clipping. Count inequalities, approximate values, missingness, invalid units, validity flags, and potential duplicates separately. Retain originals and source pChEMBL for comparison. These are proposed screening contracts for this phase, not approval of the final curation policy.

The initial biological compatibility hypothesis is human AChE catalytic inhibition in cell-free enzyme preparations. Distinguish recombinant enzyme, erythrocyte enzyme preparation, intact cells, reactivation, nonhuman enzyme, mutants, and unclear context. An organism expression host is not automatically the protein's species. An assay label such as binding is not sufficient evidence of compatible conditions.

Record substrate/readout, enzyme preparation, incubation, and available pH/temperature. Classify identifiable Ellman/acetylthiocholine methods, other described methods, and insufficient descriptions separately. Whether to require one method family for the final dataset is an output recommendation, not an assumption that every metadata-screened record is comparable.

### Minimum chemical identities

Implement and test a conservative, explicitly versioned profiling transformation within this phase:

- Parse and sanitize source structures, retaining source SMILES and all failure reasons.
- Remove only identified counterions/solvents using a recorded fragment list; flag multiple plausible active components rather than choosing the largest silently.
- Normalize representations and use deterministic charge handling while preserving permanent charge and reported stereochemistry. Log changed structures. Unsupported cases stay outside usable-count claims.
- Assign a canonical isomeric parent identity for counting, keeping resolved stereoisomers and unspecified stereochemistry distinct.
- Separately form a conservative stereo-insensitive, canonical-tautomer parent equivalence key for split feasibility, including shared source parent mappings. This grouping does not merge labels. Report identity count and equivalence-group count separately.
- Calculate nonchiral Murcko scaffolds and linked groups that prevent an equivalence family from being divided by scaffold representation. Keep acyclic molecules in one explicit group for this diagnostic and report its size.

Record toolkit version, transformation parameters, identity and grouping rules, and failures. Test salts, equivalent SMILES, stereoisomers, tautomers, charged compounds, ambiguous mixtures, invalid structures, and acyclic molecules. Compare source-molecule counts with identity/group counts so the effect of these choices is visible. Phase 2 may refine the rule after reviewing this evidence; a revision produces a new profile identity.

The implementation plan's chemistry contract resolves the exact ordered operations, fragment list, charge and tautomer policies, source-parent validation and connected-component algorithms before test implementation. Measurement-summary identities never become merged merely because they share conservative leakage groups. Missing source-parent information is flagged and falls back to structure-derived grouping; conflicting mappings are preserved and quarantined from diagnostic usable populations, not silently discarded. Toolkit functionality supplies chemistry operations; independently justified chemical relations supply test expectations.

### Repeat measurements and split feasibility

An extraction-artifact duplicate is a repeated `(source archive identity, activity_id)` with identical canonical source payload (field order and transport/run metadata excluded; source field values and nulls preserved). Keep one scientific row and record repeated encounters in the run audit. The same key with differing source payload is an integrity error, not an alternative measurement. Distinct activity keys remain separate source records even when all measured values, assays or documents match. Do not collapse them without explicit source evidence of a shared observation. If such evidence exists, add a versioned evidence-linked observation relationship while retaining both records; Phase 1 does not collapse those records in its primary descriptive summaries.

Report counts of source activity records, distinct assays, distinct documents, and compounds with multiple source records. None establishes experimental independence. Report source-flagged duplication, suspected duplication and evidence-linked shared observations separately, allowing overlap and unknown status. Equal values are never sufficient to identify a duplicate. Within-assay/between-assay dispersion describes source-record variation, not independent experimental replication.

Report distributions of ranges and other robust descriptive summaries without declaring a final compound label. A singleton is not evidence of agreement. Do not apply the original one-log cutoff or aggregation method as an approved final policy. The phase report can justify candidate choices from assay context and repeat coverage before any model scores exist.

Profile group sizes, largest-group fraction, scaffold counts, acyclic fraction, and document concentration. Use diagnostic allocations only to expose whether usable train/validation/test partitions are possible under whole-group constraints. Proposed diagnostic default: 70/15/15 with one fixed recorded seed, no label balancing and no repeated search for favorable allocations. These are not the final evaluation splits and are not used for model selection. Retain the diagnostic assignment and its algorithm revision as evidence.

Produce separate profiles for all extracted records, metadata-screened candidates, and manually reviewed compatible records. Never multiply a convenience-sample acceptance rate by the full dataset to claim a final usable count.

## 6. Bounded assay-review protocol

**Proposed budget:** at most **120 distinct assays or six hours of active review**, whichever comes first, including any source-document consultation. At most **20 accessible source documents**, with no more than **10 minutes per document** inside the same six-hour total. This is a proposed initial workload cap, not a claim that the entire dataset can be curated in that time. Track actual time and unresolved work.

Before inspecting potency values or model outcomes, freeze the review list from metadata-screened AChE assays:

1. Freeze up to 60 high-coverage assays in descending distinct source-molecule coverage, breaking ties by assay ID. Coverage counts metadata-screened target/endpoint records without filtering or ordering by potency value.
2. Freeze up to 60 additional assays from the remaining set using seed 17 and pre-review strata: stored `bao_format` (each nonempty code, or `UNKNOWN`) crossed with source document year (`BEFORE_2000`, `2000_2009`, `2010_2019`, `2020_PLUS`, `UNKNOWN`). Missing/unparseable years use UNKNOWN. Stored format codes are sampling attributes, not trusted manual method classifications. Within each stratum order by the SHA-256 of canonical `[17, source_id, assay_id]`, where source_id includes the pinned release and archive hash; visit strata in lexical order round-robin until 60 assays or exhaustion. This avoids post-review knowledge in selection.
3. Interleave the frozen lists as H1,S1,H2,S2,...; once either list ends, append the other list's remaining entries. Freeze this order and both selections before review. If fewer than 120 candidates exist, select all available candidates without replacement. Stop at a cap, at list exhaustion, or earlier for an evidence-linked decisive blocker. The budget is a cap, not a quota. On a resumed approved review, preserve the unvisited suffix rather than reseeding.

This is coverage-oriented reconnaissance, not an unbiased estimate of all assays. Record reviewed fractions of assays, activities, compounds, documents, and scaffold groups. Within the reviewed subset, accepted records provide an observed compatible subset; unreviewed records contribute only to a candidate upper bound. If time expires partway through the list, preserve the original selection order and mark the remaining assays unreviewed.

Assay compatibility is only one eligibility condition. A record enters a reviewed usable population only if its assay decision is compatible/confirmed AND its own metadata, numerical value and structure pass the record-level contracts. An assay decision never overrides record-level contradictions, missing structures, censoring or invalid measurements. Coverage reporting must use this intersection, not every record from an accepted assay.

Each decision includes release/assay/document IDs, structured metadata, description/reference supporting it, reviewer, timestamp, category, rationale, and missing evidence:

- **Compatible under the profiling hypothesis:** affirmative evidence of the defined human enzyme-inhibition context and an identifiable method.
- **Incompatible:** affirmative evidence of another species, response, variant, or conflicting biological context.
- **Unresolved:** insufficient evidence, inaccessible source, or unresolved contradiction. A structured human/confidence-9 label does not override an eel description.
- **Unreviewed:** not assessed within the frozen list/budget; distinct from unresolved.

Do not infer missing protocols, bypass access restrictions, or represent an automated keyword screen as expert validation. An assistant may propose evidence-linked decisions; identify who reviewed them and distinguish machine-proposed decisions from human-confirmed decisions. Surface consequential interpretation disputes to the user before counting them as confirmed compatible. Review choices must not use potency magnitude or future prediction quality to prefer assays.

If reviewed evidence is too sparse to support the scope, report inconclusive. Recommend either a specifically bounded extension or an EGFR feasibility design amendment; neither happens automatically. Exhaustive review belongs only in a later approved scope with a realistic effort estimate.

## 7. Deliverables and acceptance criteria

| Deliverable | Acceptance evidence |
|---|---|
| Environment/readiness record | Executed checks and actual resources; compatible isolated dependency lock; successful chemistry smoke check; clear unavailable capabilities. |
| Verified source and extraction manifest | Archive checksum/version match, source notices retained, reproducible target extraction, no duplicate activity keys or silent join loss. |
| Minimal profiling workflow | Independently runnable extraction, validation, identity, grouping and descriptive profiling; no dependency on PostgreSQL, Airflow, models, or later phases. |
| Assay-review ledger | Frozen selection, evidence-linked decisions and reviewer status, time/document/assay caps respected, unreviewed and unresolved records explicit. |
| Feasibility report | Counts at each stage; structure failure/merge rates; reviewed coverage; repeat and scaffold distributions; diagnostic partition sizes; resource/review effort; supported/not-supported/inconclusive conclusion with rationale. |
| Reproducibility evidence | Two runs with identical source/rule/environment inputs reproduce logical records, identities, group assignments and counts; excluded timestamps are identified; all outputs traceable to complete manifests. |
| Phase 2 handoff | Recommended target/endpoint and compatibility scope, candidate curation questions, remaining risks, and interfaces expressed as data contracts rather than future file scaffolds. |

**Engineering acceptance is not conditional on a favorable scientific result.** All extracted records have an accounted screening disposition and source key. No unresolved/unreviewed records enter confirmed-compatible counts. No fixture is misrepresented as a captured source response. Required tests pass, or phase completion is explicitly blocked on the failing requirement.

**Scientific exit assessment:** no inherited numerical pass/fail thresholds or power claims. Complete the following evidence matrix, with a reviewer-confirmed status for each criterion:

| Criterion | Required evidence and interpretation |
|---|---|
| A. Coherent reviewed prediction population | Define species/target/endpoint, assay context and compatible method strata; show reviewed usable records/identities and unresolved coverage. State whether pooling is scientifically defensible or requires narrowing to a named stratum. Metadata-screened volume alone is insufficient. |
| B. Practical whole-group allocation | Show actual train/validation/test records, identities and groups for both diagnostics, largest groups, empty/degenerate partitions, response spread and dependence/coverage limitations. Explain whether held-out estimates could be interpretable with these allocations; nonempty partitions alone do not establish adequacy. One greedy diagnostic failure is not proof that all allocations are impossible; distinguish structural impossibility from unresolved algorithm/allocation limitations. |
| C. Meaningful prespecified curation comparison | Identify the proposed intervention, records/identities it actually changes, repeat/flag evidence, training population changes, and the common held-out population with a fixed reference-label rule proposed for later approval. Show that it addresses a scientifically interpretable question; do not manufacture a contrast from sparse or ambiguous repeats. |

Use supported only when cited evidence addresses the criterion with explicit limitations; not supported requires affirmative evidence against the proposed scope; insufficient/ambiguous evidence is inconclusive. Derive two conclusions: **prediction appears feasible** when A and B are supported, and **the proposed curation-and-splitting study appears feasible** only when A, B and C are supported. If a required criterion is not supported, the corresponding conclusion is not supported as scoped; otherwise any unresolved required criterion yields inconclusive. Retain all criterion-level findings regardless of the aggregate result.

Before profiling, register a candidate contrast concerning inclusion versus exclusion of source-flagged potential-duplicate records, keeping all other eligibility rules fixed. Phase 1 measures contrast support and population overlap only; it does not build final labels or models. The plan specifies the candidate common-population/reference-label proposal. Disagreement/aggregation contrasts remain separate hypotheses requiring adequate repeat/context evidence and a separately justified protocol; no one-log threshold is reinstated. If repeat evidence cannot support them, explicitly narrow the research question to the supported curation choice, subject to phase-exit approval. If even the registered candidate lacks an affected population or interpretable reference, C is not supported or inconclusive as warranted, even if prediction remains feasible. Do not substitute another contrast silently after inspecting results.

## 8. Tests and validation design

All reusable behavior will follow red–green–refactor during approved implementation. This draft defines test intent; exact test files and execution order are deferred to the implementation plan.

| Requirement | Tests |
|---|---|
| Source integrity | Synthetic archive checksum mismatch, wrong release/schema, unsafe archive member, truncated acquisition and corrupt cache; none becomes a complete manifest. |
| Extraction correctness | Miniature SQLite source with multiple target components, missing structure/document, repeated keys and mixed endpoints; exact expected counts and explicit dispositions. |
| Eligibility | Human target/nonhuman assay, ignored-request-filter counterexample, confidence 8, missing organism, contradictory description, reactivation, and compatible cell-free example. |
| Numerical handling | Known nM/uM/pM conversions and log values; inequality, approximate relation, zero/negative/nonfinite/missing value, invalid unit and validity flags remain accounted. |
| Identity and scaffolds | Equivalent representations/salts, distinct stereoisomers with shared equivalence group, tautomer grouping, permanent charge, mixtures, invalid structures, and acyclic group behavior. |
| Repeat summaries | Repeated extraction of the same activity key does not increase source-record counts; conflicting payload under one key fails; equal-valued distinct activity keys remain separate; flagged/suspected duplication and singleton/dispersion summaries correct without independence claims. |
| Review coverage | Both selections frozen and interleaved; pre-review strata include UNKNOWN; no potency used for ordering; early blocker/cap stop recorded; time expiry does not imply scientific failure; assay acceptance cannot bypass record exclusions. |
| Split diagnostics | Whole identity/equivalence groups remain together; scaffold-linked groups do not overlap for scaffold allocations; a dominant group visibly prevents requested sizes; input-order invariance. |
| Persistence/rerun | Interrupt before manifest publication; incomplete bundle invisible, prior bundle readable; reruns verify immutable bytes/logical content without rewriting; only run metadata changes with timestamps; changed semantic review/configuration produces new identity. |
| End to end | Offline synthetic archive through all profiling stages and report; then opted-in small real-source contract validation; full candidate profile only during approved execution. |

Synthetic fixtures are labeled and independently authored with explicit expected outputs. Any captured fixture has original bytes, release/retrieval metadata and appropriate source notices; expected transformations are kept separately. Routine tests stay offline. Network/source checks are explicitly separated and cannot masquerade as passing offline tests.

## 9. Material decisions for review and recommended defaults

| Decision | Recommended default | Consequence / alternative |
|---|---|---|
| Phase 1 source access | Official pinned archive during approved execution | Larger one-time download, but complete target profiling. API-only reconnaissance leaves archive feasibility unresolved. |
| Assay-review effort | 120 assays / six hours, maximum 20 documents within that cap | Bounded effort may legitimately yield inconclusive evidence. A larger review requires a specific extension. |
| Candidate and fallback | Assess AChE IC50 first; propose an amendment before EGFR investigation | Keeps this phase bounded; avoids treating a previous fallback suggestion as blanket authorization. |
| Feasibility judgment | Evidence review at phase exit; earlier numerical thresholds remain unapproved | Preserves scientific judgment with explicit observed counts, coverage and constraints. Hard cutoffs can be agreed before execution if the user prefers. |

Routine defaults: immutable local artifacts, one reference environment, deterministic recorded diagnostic selection/seed, no model fitting, offline synthetic tests, manifest-last publication, and explicit unresolved categories. Exact dependency versions and module boundaries are implementation-plan decisions within this scope.

Questions to resolve from Phase 1 evidence include actual resource readiness, protocol-compatible coverage, chemical grouping effects, repeat-measurement availability, final curation/aggregation choices, sample adequacy, and the full-review effort needed for Phase 3. These are planned research outputs, not missing instructions that prevent drafting this design.

## 10. Approval and change control

The user has authorized revising this specification and writing its implementation plan in this turn. The new exact chemistry contract and candidate curation contrast are explicit planning proposals, not implicit final scientific approval. After the plan is ready, request explicit plan approval and the user’s choice of subagent-driven or inline execution before any development. Follow applicable TDD Guard instructions during development and report enforcement limits honestly.

Record approved revisions and material amendments. The final curation/evaluation protocol must be fixed before model selection/final evaluation intended to support the study. Phase 1 descriptive evidence may inform that protocol; predictive outcomes cannot retroactively define it. No implementation, installations, or full downloads occurred as part of drafting this specification.
