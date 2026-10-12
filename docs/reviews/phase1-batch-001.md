# Phase 1 assay review — batch 001

Status: **two dispositions confirmed; eight decisions remain assistant-proposed**.
The user explicitly confirmed assay 2351073 as compatible at assay level, retaining
the full-methods limitation. See the [confirmation record](phase1-batch-001-confirmations.md).
The user also [confirmed 902584 as unresolved](phase1-batch-001-confirmation-902584.md);
confirmation of uncertainty does not make that assay eligible.
Updated 2026-10-12 UTC (October 11 local). Record eligibility has not yet been
recomputed for the new review snapshot; no usable-population count is asserted here.

The hypothesis is human AChE catalytic inhibition in a cell-free enzyme
preparation. Metadata alone cannot establish that context. These proposals use
the pinned assay descriptions and associated publication metadata/abstracts;
**no publication full text was consulted**. No potency values or model outcomes
were used to decide compatibility. Missing evidence remains unresolved.

## Frozen selection and evidence

Source: ChEMBL 37, archive SHA-256
`33c203740555f96067710cdfc1c3c55d890660e5908ec5cbf5817492c290d281`.
Selection digest:
`945acff786c604947dc01d973e1ddd2f7f9989623e3de5313ab952de909ede61`.
The batch is the first ten entries of the frozen H/S interleaving, not a newly
selected convenience subset. The remaining 110 entries are unreviewed.

Local source evidence:

- [Complete captured target/assay payloads](../../data/chembl37/candidate-extracts/e660b9a6316572c4ae70db515c2934e39957df9c0c9b2e6e565e57d4d8a36794/raw-target.json), SHA-256 `29aedd3f022d0b876c21659654dafae296e3cf3ac8b55ca351405000bdecb834`.
- [Captured document metadata](../../data/chembl37/review-selections/951ffa8535f29147f4a230fad3400bc0d03aa044ee9720523c09c89e9e99d49f/documents.json), SHA-256 `fd30d630a4d73f43bcbb9d2a0fc9a74fd96bfc7b17262600260c7aa5f8fa1b89`.
- [Frozen queue](../../data/chembl37/review-selections/951ffa8535f29147f4a230fad3400bc0d03aa044ee9720523c09c89e9e99d49f/selection.json).

These data files are local, ignored artifacts and are not synthetic fixtures.
Source attribution: EMBL-EBI ChEMBL, release 37, CC BY-SA 3.0; retained release
license is under `data/chembl37/`. Publication links below identify the associated
source, not a claim that its full text was read.

## Decisions proposed for review

| Order | Assay (source ID) | Proposal | Evidence and remaining limitation |
|---|---|---|---|
| H1 | CHEMBL3047076 (902584) | Unresolved — human-confirmed | The assay description explicitly leaves enzyme origin unknown. Ellman's method is identified, but the associated 3D-QSAR study does not establish a common human enzyme preparation for the underlying records. [Document 68966](https://doi.org/10.1007/s00044-010-9516-x). Need original measurement provenance and enzyme origin. |
| S1 | CHEMBL828047 (305601) | Unresolved | Description identifies AChE from human erythrocytes. It does not establish whether this is a cell-free preparation or intact cells, or provide sufficient method detail. The abstract supports human AChE inhibition but does not resolve preparation. [Document 21557](https://doi.org/10.1021/jm0496741). |
| H2 | CHEMBL4770653 (2089390) | Unresolved | Ellman's method and substrate are described, but enzyme origin is explicitly unknown. The abstract does not resolve species/preparation. [Document 119819](https://doi.org/10.1016/j.ejmech.2020.112415). |
| S2 | CHEMBL4329316 (1829442) | Unresolved | Human erythrocyte AChE and Ellman's method are described. Preparation versus intact cells remains unclear. The abstract's Torpedo crystallography is a different experiment and is not by itself evidence that this inhibition assay is nonhuman. [Document 110966](https://doi.org/10.1016/j.ejmech.2018.10.064). |
| H3 | CHEMBL832763 (305174) | Unresolved | General human AChE inhibition description; associated docking study discusses compiled inhibition constants. Need measurement-level origin, endpoint correspondence and preparation. Do not infer that IC50 records are Ki or predicted merely from the abstract. [Document 21147](https://doi.org/10.1021/jm049695v). |
| S3 | CHEMBL5216393 (2261382) | Incompatible with current scope | Description explicitly identifies whole human red blood cells. That conflicts with the prespecified cell-free preparation scope. This does not mean the measurements are invalid. [Document 124832](https://doi.org/10.1016/j.ejmech.2022.114606). |
| H4 | CHEMBL1664219 (715113) | Unresolved | General human AChE inhibition description, associated with a QSAR study. Need original experimental preparation and record-level distinction between compiled measurements and prospective predictions; neither is established by the assay label. [Document 55218](https://doi.org/10.1016/j.ejmech.2010.10.009). |
| S4 | CHEMBL644627 (28629) | Unresolved | Assay description identifies human erythrocyte AChE; abstract also discusses rat/eel experiments. A multispecies publication is not enough to invalidate the human assay. Need the human assay protocol and cell-free preparation evidence. [Document 15335](https://doi.org/10.1021/jm981101z). |
| H5 | CHEMBL5362186 (2351073) | Compatible at assay level — human-confirmed | Description identifies recombinant human AChE, acetylthiocholine substrate, preincubation and Ellman's method. This supports the cell-free catalytic inhibition hypothesis. The paper's BChE focus does not negate its separately described AChE assay. Full methods/supporting information have not been independently checked. Pooling across methods is still for phase-exit assessment. [Document 127580](https://doi.org/10.1016/j.ejmech.2023.115301). |
| S5 | CHEMBL1051649 (578532) | Unresolved | Ellman's method is identified, but inhibition described in human erythrocytes does not resolve intact-cell versus enzyme-preparation context. [Document 47755](https://doi.org/10.1021/jm900859q). |

Remaining recommendation: review the whole-cell exclusion and the seven remaining
unresolved proposals individually. Assays 2351073 and 902584 no longer need disposition confirmation. You may amend
individual entries by assay ID. Confirming an unresolved
entry confirms only its unresolved disposition, not its eligibility.

Assay acceptance never overrides numerical censoring, missing/invalid structures,
record exceptions or allocation quarantine. No reviewed-usable record count is
claimed here. The source-warning contrast and final aggregation remain provisional.

## Review effort and next steps

Initial inspection of these ten assay descriptions and associated metadata ran
from 2026-09-26 18:02:24 UTC to 18:03:11 UTC (47 seconds). This is the measured
initial inspection interval, not a claim of ten full-paper reviews. Document
consultation remains necessary for the unresolved cases. Drafting this decision
record is also charged to the review cap: the saved ledger conservatively charges
the entire elapsed session from 18:02:24 to 18:06:49 UTC (**265 seconds**), including
intervening implementation work, as an upper bound. This replaces rather than
duplicates the initial 47-second interval. It is not a precise allocation of time
to individual papers. Ten publication metadata/abstract entries were inspected;
zero external full texts were opened. Future source-document consultation must be
timed separately. Waiting for user confirmation is excluded.

The [proposed ledger](../../data/chembl37/review-ledgers/batch-001-proposed.json)
was imported into [immutable review snapshot 4fdcbab9](../../data/chembl37/review-state/reviews/4fdcbab9a890faf7c498a3d722c356706a5d7c449494d817f0e268da96d5cb5b/reviews.json).
That original snapshot retains all ten `assistant_proposed` states unchanged.

The [updated ledger](../../data/chembl37/review-ledgers/batch-001-confirmed-2351073.json)
was published as [review snapshot 21ef698d](../../data/chembl37/review-state/reviews/21ef698d86b28d9060dc527d345fd2ab536a2617b29acef8ddb0a636ac658f78/reviews.json).
In that snapshot only 2351073 is `human_confirmed`; the other nine decisions and
the frozen queue were unchanged.

The subsequent [ledger confirming 902584 unresolved](../../data/chembl37/review-ledgers/batch-001-confirmed-2351073-902584.json)
was published as [review snapshot d5bcdef7](../../data/chembl37/review-state/reviews/d5bcdef7b33e1a0fb0b92446f6010c5117904966f3770a41f1e3902567d06aa5/reviews.json).
It preserves 2351073 as confirmed compatible and changes only 902584's confirmation
state and confirmation provenance. Eight decisions remain proposed, and the frozen
queue is unchanged. `config/phase1.json` now references this snapshot. Existing
profiles and interim assessments still describe their original input snapshots.

No decisive scientific blocker or budget exhaustion is declared. Human
confirmation, broader review coverage, record-level eligibility, and criterion
evidence are still required before a Phase 1 exit decision.
