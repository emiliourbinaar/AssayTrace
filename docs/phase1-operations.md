# Phase 1 operations — in development

The profiling CLI supports the authored synthetic fixture only; `review-import`
also accepts local review ledgers. The pinned ChEMBL
archive has been verified and extracted, and a bounded source adapter check has
passed. The synthetic CLI now publishes molecular identities and provisional
structure groups as well as numerical results. Programmatic full-target extraction,
recursive parent-context extraction and candidate chemistry/grouping have now run
against the local pinned source. Their outputs are provisional evidence bundles;
the real-profile CLI, complete validation and human-confirmed assay review remain
unfinished.

## Reference environment

Windows uses Docker Desktop's Linux engine. Python 3.12 and the base-image digest
are pinned in `Dockerfile`; `uv.lock` records resolved dependency hashes.
`requirements.lock` is generated from that lock for the hash-checked Docker build.
RDKit, NumPy and Pillow are installed because the approved chemistry toolkit
requires them; no models or orchestration services are installed.

In PowerShell at the project root:

```powershell
$env:PATH = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin;" + $env:PATH
docker build -t assaytrace-phase1:test .
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace" -w /workspace assaytrace-phase1:test python -m pytest tests -q
```

The second command runs unit and synthetic integration tests offline, including
the subprocess CLI. Tests build their own temporary SQLite fixtures. The image
tag is a convenience; exact observed digests are in `phase1-validation.md`.

For an existing synthetic fixture matching `tests/conftest.py`:

```powershell
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace" -w /workspace -e PYTHONPATH=src assaytrace-phase1:test python -m assaytrace profile --synthetic --source /workspace/data/synthetic.sqlite --output /workspace/artifacts/synthetic
```

This does not create or authenticate a ChEMBL source. Outputs live under
`profiles/<profile_id>/`, with separate execution records under `runs/`.
Incomplete `.stage-*` directories are not published profiles. Do not delete or
repair immutable bundles automatically. Changed incoming output under the same
specification is an error, even when the existing bundle is intact.

The pytest reporter writes `.claude/tdd-guard/data/test.json`. Automatic
write-blocking enforcement has not been demonstrated; explicit TDD evidence is
recorded in the validation log.

## Opt-in local source compatibility check

After the approved archive has been checksum-verified and extracted, run:

```powershell
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace" -w /workspace -e ASSAYTRACE_CHEMBL37_SQLITE=/workspace/data/chembl37/extracted/chembl_37/chembl_37_sqlite/chembl_37.db assaytrace-phase1:test python -m pytest tests/source/test_chembl37_contract.py -q
```

This reads at most 20 IC50 activities from the first 20 target assays and checks
them against captured source IDs and direct primary-key reads. It makes no
network requests, performs no model fitting and establishes no scientific
eligibility. Without the environment variable the source test is skipped.
The captured diagnostic evidence lives under ignored `data/chembl37/`; authored
offline fixtures remain separately labeled in `tests/fixtures/README.md`.
## Local review snapshots

Inside the reference container, `python -m assaytrace review-import --selection
selection.json --ledger ledger.json --output output` reads local files only.
The selection is the complete frozen `review_queue` output, including its digest.
The ledger is a cumulative snapshot with `decisions`, `active_intervals`, and an
optional `stop`. Each decision supplies source_id, assay_id, category
(compatible/incompatible/unresolved), confirmation_state
(assistant_proposed/human_confirmed), evidence_refs, and record_exceptions.
Reviewer and reviewed_at fields are optional audit metadata. Only actual explicit
human review authorizes human_confirmed; the importer preserves the supplied state
and cannot independently establish who approved a file.

Active intervals have timezone-aware ISO `start` and `end`, and optional
document_id. Include prior intervals when resuming; do not reset the budget in a
new ledger. Partial decisions stay unresolved, and absent decisions stay
unreviewed. An optional decisive_blocker stop supplies evidence_refs, explanation
and confirmation_state; it is not itself a scientific feasibility verdict.

The command prints artifact references. Scientific snapshots are immutable under
`output/reviews/`; execution and review audit records are separate under
`output/runs/`. Resume by importing an updated cumulative ledger with the same
selection. Changed scientific decisions create a new snapshot; old snapshots are
retained. The actual 120-assay source queue is now frozen. Batch 001 has ten
assistant proposals and 110 unvisited entries; no human-confirmed ledger has
been produced.

## Real-source evidence checkpoint, 2026-09-26

Read-only helpers `extract_target_candidates`, `extract_molecule_context` and
`extract_documents` in `assaytrace.extract` were run against the already verified
local SQLite file. `molecular_context_profile` combines the approved chemistry
wrapper with the full source-parent graph. `assay_sampling_rows` and `review_queue`
produce the frozen review order without potency filtering. No models ran.

Ignored local evidence directories:

- `data/chembl37/candidate-extracts/e660b9a6.../`: complete target/IC50 activity
  payloads and all target assay metadata.
- `data/chembl37/molecule-contexts/95d096c1.../`: candidates and recursive parents,
  with original molecule/structure/hierarchy payloads.
- `data/chembl37/candidate-chemistry/eef8e7f3.../`: standardized molecules and
  grouping evidence before assay review.
- `data/chembl37/review-selections/951ffa85.../`: frozen queue, sampling metadata
  and source document context.
- `data/chembl37/review-state/reviews/4fdcbab9.../`: ten unconfirmed proposals.

Each directory has a completion manifest and byte/logical hashes. Extraction/run
records are separate. These programmatic executions do not substitute for the
remaining end-to-end phase acceptance checks. The local profile CLI added below
now composes these stored inputs; it does not repeat extraction from SQLite. See
[batch 001](reviews/phase1-batch-001.md) for full evidence paths and pending human
decisions. Do not mark assistant proposals human-confirmed merely to run a profile.

## Profile existing release bundles

`config/phase1.json` references the four immutable candidate, molecular-context,
frozen-selection and review manifests from the checkpoint. Paths are relative to
the descriptor file, so the same descriptor works inside the reference container.
The data files are local, ignored artifacts, not included in a fresh clone.

```powershell
docker run --rm --network none --mount "type=bind,source=$PWD,target=/workspace" -w /workspace -e PYTHONPATH=/workspace/src assaytrace-phase1:test python -m assaytrace profile --inputs config/phase1.json --output data/chembl37/reviewed-profiles
```

This verifies stored bundle inventories, hashes, canonical JSON, source identity,
target/endpoint, context-to-candidate links and frozen review provenance. It then
recomputes chemistry, full-context groups, record eligibility, repeat summaries
and allocation/contrast diagnostics. Publication compares new output with any
existing bundle under the same specification; changed output fails without
overwriting it. Source records with equal values remain separate. Conflicted
parent groups remain descriptive measurements when their other eligibility gates
pass, but cannot enter allocation. Unconfirmed reviews never authorize records.

On 2026-10-10 the user explicitly deferred review: keep batch 001 assistant-proposed.
The descriptor therefore still references that snapshot. Empty reviewed counts
are pending evidence, not a scientific failure verdict. `scientific_assessment`
remains `not_performed`; no models are fitted. Updating review decisions requires
an actual approved ledger and a newly published review snapshot, then changing
the descriptor reference. Never edit the old bundle.

`read_bundle` reports `stored_integrity_only`. The CLI actually recomputes the
profile, and an identical rerun reports `reconstruction_compared`; that comparison
is limited to reconstruction **from stored extraction artifacts**. Neither mode
authenticates arbitrary source contents or proves independent archive extraction.
The source ID is checked against the approved ChEMBL37 release hash, and input
manifest hashes enter the profile specification. Synthetic bundle inputs require
`--synthetic` and retain explicit `not_established` source compatibility.

See [profile data dictionary](phase1-profile-data-dictionary.md) for output grains
and interpretations. Acquisition and criterion-assessment CLI commands, fuller
source relationship validation, independent archive re-extraction and the final
scientific exit assessment remain pending; this is not Phase 1 acceptance.
