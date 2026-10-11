# AssayTrace project roadmap

**Status:** Overall project direction approved. Phase 1 specification and implementation plan approved for inline execution; Phase 1 is in progress and has not passed scientific exit review. Later phases remain separately gated. Status updated 2026-10-11; roadmap scope remains unchanged.

## Purpose and scope

**Research question:** How do bioactivity curation choices and molecular train/test splitting strategies affect measured predictive performance?

Build a focused portfolio system demonstrating structured scientific data, SQL, reproducible ETL, orchestration, cheminformatics, and defensible modeling. Complement biomedical literature work with a completed structured-data analysis. Successful delivery requires credible evidence and reproducibility, not improved model scores or a polished frontend.

The intended scientific scope is one pinned ChEMBL release, one target, and one endpoint. Compare a small number of justified curation policies, one simple baseline and one stronger model candidate, and random versus scaffold splitting. Human AChE IC50 and ChEMBL 37 are the initial candidates; their detailed adoption depends on Phase 1 findings and approval. EGFR IC50 is a possible fallback to assess, not an automatic switch.

## Scientific safeguards

- Preserve original source material and all transformations, exclusion reasons, and label lineage. Distinguish source activities, source molecule IDs, standardized compounds, and scaffold groups.
- Keep endpoints and biological contexts explicit; never silently combine IC50, Ki, or EC50, species, or incompatible assays.
- Keep identical standardized compounds and agreed equivalence groups out of multiple partitions. Apply scaffold-group separation for scaffold evaluation.
- Fit learned preprocessing on training data only. Keep model selection separate from final test evaluation.
- Use a common held-out population and fixed labels for paired curation comparisons. Disclose changes in training size, coverage, and test populations; do not attribute those changes automatically to improved modeling.
- Define the scientific protocol before final experiments. Preserve negative findings, uncertainty, and limits of scaffold-based evaluation.
- Changes informed by feasibility evidence are allowed with an explicit rationale and approval where material. Changes after viewing final test results are amendments or exploratory analyses, not silent replacements of the original experiment.

## Architectural direction

Independently testable Python transformations perform extraction, curation, dataset creation, and model evaluation. PostgreSQL provides relational storage and queryable lineage; Parquet provides versioned analytical artifacts. Airflow orchestrates ordinary package functions and exchanges references to stored artifacts. Docker Compose provides a reproducible local environment on Windows through Linux containers.

This is a direction, not a frozen service layout or package-version list. Phase designs justify concrete dependencies and contracts. Phase 1 uses the minimum tools needed for evidence; the curated data vertical slice introduces persistent SQL storage and thin orchestration. Basic idempotency, integrity verification, and publication safety accompany the first persisted artifacts and dataset. Final acceptance strengthens and validates these properties.

```mermaid
flowchart LR
  P1[1. Foundation and feasibility] --> P2[2. Curated data vertical slice]
  P2 --> P3[3. Complete versioned dataset]
  P3 --> P4[4. Predictive evaluation]
  P4 --> P5[5. Operational and portfolio acceptance]
```

## Phases and exit evidence

| Phase | Outcome | Evidence required before advancing |
|---|---|---|
| 1. Foundation and scientific feasibility | Reproducible profiling environment, pinned-source access, minimal tested extraction/identity/scaffold profiling, bounded assay assessment | Traceable feasibility report distinguishing supported findings from uncertainty; target/protocol recommendation; resources and review effort measured. No dependency on later phases. |
| 2. Curated data vertical slice | Small source subset through agreed scientific rules, PostgreSQL, Parquet, lineage, and a thin Airflow ingestion flow | Approved data contracts work end to end; exclusions reconcile; persistence is safe and reruns do not duplicate data. |
| 3. Complete versioned dataset | Full selected-target curation under approved policies with versioned outputs | Complete curation/coverage report, validated identity and lineage, reproducible dataset, documented remaining scientific limitations. |
| 4. Predictive evaluation | Approved protocol, grouped splits, baseline and stronger candidate, model selection, uncertainty, reports | Leakage and isolation checks pass; all planned experiments and relevant negative results reported; population changes visible. |
| 5. Operational and portfolio acceptance | Recovery demonstrations, clean-environment reproduction, scientific interpretation and documentation | Another reader can reproduce the local demo and approved full analysis and trace results to source evidence. |

Detailed design for Phases 2–5 is intentionally deferred. Their interfaces and implementation steps will reflect the preceding phase's validated outputs. Phase reports may recommend revising the roadmap rather than forcing a positive feasibility result.

## Workflow and authority

For every phase:

1. Use Superpowers brainstorming to explore requirements, alternatives, and material open questions.
2. Present a phase design specification for user approval or revision.
3. After spec approval, use Superpowers writing-plans to prepare its implementation plan.
4. Obtain explicit implementation-plan approval and ask whether the user prefers subagent-driven development or inline execution. These may be answered together; neither is inferred from roadmap approval.
5. Develop with red–green–refactor and applicable TDD Guard instructions, recording meaningful test failures and subsequent passing checks.
6. Validate the phase, report findings and deviations, and use that evidence to design the next phase.

The current `AGENTS.md` supplies the Superpowers and execution-choice instructions. The user's explicit request also requires implementation-plan approval. Resolve that combination by requiring both plan approval and execution choice before development. Do not ask for an execution mode while the design is still awaiting approval.

Each document records its status and approved revision. A requirement change affecting scientific meaning, scope, or interfaces returns to design review. Routine implementation choices within the approved plan do not require repeated permission. The original roadmap reorganization was documentation-only; Phase 1 subsequently received its separate specification, implementation-plan and inline-execution approvals.

## Decisions deliberately left provisional

Target/protocol details; minimum sample sizes; treatment of repeated/disagreeing measurements; aggregation; molecular standardization; model family/settings; exact split allocation and seeds; uncertainty method; storage schema; package versions; service layout; and runtime estimates require justification in the relevant phase design. The initial proposal supplies options and historical reasoning, not binding values.

The scientific protocol is fixed before final evaluation and should also precede model selection runs intended to support final claims. Record version, rationale, timing relative to data/result access, approval, and affected artifacts for amendments. Historical results are retained.

## Project acceptance and scope limits

Delivery includes a reproducible local setup and small offline demo; pinned source and versioned modeling data; relational schema/data dictionary; architecture diagram; curation report with reconciled counts and provenance; evaluation report with population definitions, uncertainty and negative findings; and an honest limitations section.

Required scientific and engineering tests pass. Demonstrate duplicate-free reruns, recovery from interrupted publication, and reproduction from the pinned source/environment. Quantitative phase criteria are justified in phase designs; no minimum predictive score defines success. If scientific feasibility fails, report the failed feasibility result and propose a scope revision rather than claim completion of the intended modeling study.

Out of scope unless a demonstrated need leads to a separately approved change: multiple targets/endpoints in the final study, LLMs, vector databases, Kubernetes, distributed processing/training, elaborate infrastructure, prediction services, frontend polish, and scheduled daily retraining for release-based data.

## Document map

- [Initial proposal and historical feasibility evidence](superpowers/plans/2026-09-11-assaytrace.md): original body retained; execution details are historical.
- [Phase 1 design specification](superpowers/specs/2026-09-11-phase-1-foundation-feasibility-design.md): approved for the bounded Phase 1 scope.
- [Phase 1 implementation plan](superpowers/plans/2026-09-12-phase-1-implementation.md): approved for inline execution.
- [Interim findings](phase1-findings.md) and [execution evidence](phase1-validation.md): scientific uncertainty and verified implementation results; not phase-exit approval.
- Future phase specifications and implementation plans will be written only at their respective workflow gates. Historical file lists, schema proposals, and commands will be reconsidered there, not copied into active future plans now.
