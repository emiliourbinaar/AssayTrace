# Phase 1 interim findings — 2026-10-11

**Status: engineering progress; scientific assessment incomplete.** This is not
a phase-exit approval request. The user deferred batch 001 review on October 10;
all ten decisions remain assistant-proposed. No model has been fitted.

The pinned ChEMBL37 human AChE/CHEMBL220 IC50 extraction contains 10,079 activity
records and 8,372 candidate source molecules. These are candidate counts, not a
reviewed prediction population. The complete source-parent context contains
9,490 molecule rows, including 1,118 auxiliary parents. Full profiling preserves
all activity payloads and keeps separate measurement and leakage-control identities.
See the [execution evidence](phase1-validation.md) for provenance and limits of
the bounded source-adapter check.

The verified stored-input reconstruction has 10,079 distinct release-qualified
activity keys. Its chemistry and grouping files match the earlier checkpoint
byte-for-byte. Identical rerun comparison preserves every original file timestamp;
a reconstruction in a separate output directory produces identical scientific
files and manifest. This evidence is limited to reconstruction from stored
extraction artifacts; independent SQLite/archive re-extraction is still pending.

| Scientific exit criterion | Current assessment proposal | Evidence and limitation | Next evidence needed |
|---|---|---|---|
| A: Coherent reviewed prediction population | Inconclusive | Frozen queue: 120 assays. Batch 001: 10 proposed decisions, 110 unreviewed selected assays, no human-confirmed eligible measurements. Candidate counts cannot substitute for reviewed compatibility. | Human review of [batch 001](reviews/phase1-batch-001.md), then bounded review/record-level accounting. |
| B: Practically usable whole-group allocation | Inconclusive | Pre-review chemistry/grouping is reproducible. Current reviewed allocation is empty because review is unconfirmed. This does not show the eventual population cannot be allocated. | Allocation diagnostics on a confirmed eligible population, including group concentration and actual train/validation/test coverage. |
| C: Meaningful prespecified curation contrast | Inconclusive | Synthetic tests distinguish row removal, lost identity membership and changed prospective medians. No confirmed real population yet supports an interpretable comparison. | Real repeat/context coverage, source-warning-policy support, restricted common-reference coverage and phase-exit review of aggregation/evaluation choices. |

Prediction feasibility (A+B) and feasibility of the curation-and-splitting study
(A+B+C) both remain **inconclusive**. These are assistant assessment proposals,
not human-confirmed scientific verdicts. We cannot yet conclude whether repeat
coverage supports disagreement/aggregation; the original question has not been
replaced by the potential-duplicate sensitivity proposal. Unknown flags remain
separate, and an unflagged reference population would be restricted, not ground
truth. No sample cutoff or disagreement threshold has been adopted.

The engineering result includes [local operations](phase1-operations.md), a
[profile data dictionary](phase1-profile-data-dictionary.md), immutable publication
and tested failure recovery. Remaining Phase 1 work includes fuller source and
evidence validation, independent source re-extraction, acquisition/assessment CLI
wiring and broader failure auditing, followed by bounded scientific review and
the three criterion assessments. Later phases remain at roadmap level.
