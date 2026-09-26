# Phase 1 execution evidence

## 2026-09-12 — Approval, corrections and reference-environment preflight

The user approved inline execution of the specification and implementation plan with bounded corrections. Incorporated: exactly one remaining component; separate grouping quarantine from measurement validity; restricted unflagged reference population; prospective identity/label sensitivity rather than record-removal counts alone; stored-integrity plus incoming-output publication comparison; and earlier bounded real-source adapter validation. Assay decisions remain proposals until explicit user confirmation.

### Commands and observed outcomes

- Read `AGENTS.md` and `.claude/tdd-guard/data/instructions.md`. The latter requires one meaningful failing test at a time and an assertion-level red before implementation.
- `Get-Command docker,uv,python`: uv and MSYS2 Python found; Docker not found on PATH.
- `Test-Path 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'`: false. This checks a standard location, not every possible installation.
- `wsl --status`: reports that Windows Subsystem for Linux is not installed and suggests `wsl.exe --install`.
- C: available bytes: 278342991872, approximately 259 GiB at inspection. Container RAM/CPU capacity is not yet verified.
- Inspected workspace contains planning documents, `AGENTS.md`, and existing `.claude` instructions; no existing application/test baseline or Git repository was found in the inspected root.

### TDD and scientific status

No application tests have been written or run, and no red/green success is claimed. The Linux reference environment is unavailable pending system installation permission. A repository TDD instructions file does not establish an installed reporter or active enforcement. Automated TDD Guard enforcement is not established; explicit red–green–refactor remains required and authorized.

No package/environment installation, application scaffold, archive download, source compatibility check, scientific profile or assay review has occurred in this execution attempt. Synthetic behavior, real-source compatibility and scientific feasibility remain unverified. The first slice is not complete.

The statements above describe the initial preflight only; the execution updates below supersede that environment status.

## 2026-09-12 to 2026-09-13 — Reference environment and initial TDD

With explicit user permission, installed WSL 2.7.14 (default version 2) and Docker Desktop 4.90.0. The elevated WSL installer and Docker installer both returned 0. Docker installer Authenticode status was Valid, signer Docker Inc.; SHA-256 was `2ecc54255702ffbf2e2779cb35ebecde535a0b31e4223171be2195dc318ebd3d`. After user-completed onboarding, `docker version` confirmed Engine 29.7.2 on linux/amd64. Host reports 34,053,414,912 bytes RAM, 32 logical processors and HypervisorPresent=True.

Created minimal environment configuration. `uv lock` resolved the approved RDKit 2026.3.6 with pytest 9.1.1 and tdd-guard-pytest 0.1.2; transitive dependencies are recorded in `uv.lock`. `requirements.lock` is its hash-bearing export, used by pip with `--require-hashes` in Docker. Python base image digest: `sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254`. Built local image manifest: `sha256:672ad70b8cfaf323cfece4f4f301b3b56d30a9990ce11ea13facc528b00c2f06` (manifest list `sha256:0e992f04fc5c68d76af654e2b3bbd5d430c32d9abc9d56859bc4df9c837653b9`). Scientific toolkit import/behavior validation is still pending.

Docker installation is outside the sandbox's readable executable paths; runs require tool escalation. The inherited shell PATH also omits Docker's credential helper; network image operations used a process-local PATH addition. No machine-wide PATH change was made by the agent.

All initial tests ran in the container with `--network none`, mounting this repository at `/workspace`. Observed red/green cycles:

| Behavior | Intended red | Subsequent green |
|---|---|---|
| Deduplicate encounters, retain distinct equal-valued source records | Empty rows versus two expected records | 1 passed |
| Reject conflicting payload under same source key | DID NOT RAISE SourceConflict | 2 passed |
| Preserve integer versus floating source payload types | DID NOT RAISE SourceConflict | 3 passed |
| Convert 1 nM to pIC50 9 | None versus 9.000000000000 | 4 passed |

The reporter wrote `.claude/tdd-guard/data/test.json` with passing test results. This verifies reporter output only, not automatic write blocking. Explicit TDD remains the enforcement method. The numerical contract is incomplete: unit handling, qualifiers and invalid values are the next behaviors. No source compatibility or scientific feasibility is established; no ChEMBL archive has been acquired.

## 2026-09-13 — Synthetic vertical slice checkpoint

Continued one new behavior at a time. The current offline suite reports **50 passed in 1.72s**. Each added behavior below was first observed failing at an assertion, then passed after its implementation. Parameterized cases exercise one shared contract per test function.

| Added behavior | Observed intended failure before implementation |
|---|---|
| Micromolar conversion and remaining approved units | Wrong scale or unrecognized unit |
| Censored, nonfinite, nonpositive, missing/malformed values and unknown units | Accepted invalid value or unclassified parser/unit error |
| Canonical UTF-8 JSON and tagged nonfinite values including arrays | Wrong bytes or bare NaN/Infinity |
| Bundle publication and unchanged rerun | No result or no reuse |
| Corrupt stored bytes, changed incoming content, extra inventory, changed stored specification | Expected integrity error was not raised |
| Interrupted write and failed fsync | Final directory exposed or sync failure not observed |
| Unsafe/reserved payload names | Accepted name or unclassified filesystem error |
| Separate run records | No execution records |
| JSONL logical metadata and its verification | Missing row count or incorrect stored count accepted |
| Synthetic CLI accounting and preserved source dispositions | Nonzero exit or missing activity artifact |
| Wrong source version and missing column | Accepted source or unclassified missing-column error |
| Missing-structure retention and no component-link multiplication | Source SMILES missing from output |
| CLI rerun and separate audit records | No run records despite preserved bundle |
| Module command entry point | Subprocess nonzero exit because entry point was absent |
| Code/environment profile provenance | Lock hash absent from specification |

Extraction and numerical profiling were refactored outside argument parsing with all existing tests passing. The synthetic fixture yields six retained activity records and four exact numerical IC50 values; those are **synthetic expectations**, not ChEMBL findings. Invalid endpoints/qualifiers retain their original payload and explicit numerical reason. Chemistry, review and source compatibility remain unassessed.

The repository was found initialized on an unborn `main` branch during this continuation. Created `phase1-foundation` without deleting or replacing existing files. Read the additional root `tdd-guard_instructions.md`, which contains the same incremental TDD requirements. No commits or remote publication have been performed.

RDKit import reported 2026.03.6 and Python 3.12.14. A separate shell smoke expression failed due to PowerShell stripping quotes around a SMILES literal; this is not a chemistry test result. Actual chemical-rule tests remain pending.

A bounded read of the official release listing and `checksums.txt` confirmed the planned archive checksum on 2026-09-13: `33c203740555f96067710cdfc1c3c55d890660e5908ec5cbf5817492c290d281`, filename `chembl_37_sqlite.tar.gz`. No archive was downloaded. Source: https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_37/checksums.txt

Remaining before claiming Tasks 1–2 complete: finish manifest/equality contracts and reconstruction-mode reporting, exercise remaining source-boundary/recovery cases, and validate reference environment identity. The first synthetic command path works but is not the completed Phase 1 system. Task 6A acquisition safeguards and actual-source adapter check follow; chemistry/review/full profiling remain later.

## 2026-09-14 through 2026-09-22 — Acquisition safeguards and resumed validation

The interrupted source-sync green step was verified on 2026-09-22 after starting Docker Desktop: **74 passed in 12.81s**, all offline. The prior full baseline was 73 passed; the additional test injects an `fsync` failure and verifies that no final source file appears. The implementation flushes and syncs the partial file before verifying the digest and renaming it.

Additional explicit red/green cycles implemented reconstruction-comparison reporting, missing-artifact integrity errors, summary JSON logical metadata and verification, and the acquisition behaviors below. Each test was observed failing before the associated implementation change.

- Streaming download through a `.part` file with an 8 GiB byte cap and 1 MiB reads.
- Checksum mismatch and HTTP Content-Length truncation rejection without final publication.
- At most three attempts for 5xx, 429 and transient connection failures; 1/2-second fallback delays; numeric and HTTP-date Retry-After values capped at 60 seconds.
- Existing source checksum verification without overwrite when a requested pin differs.
- Pre-extraction rejection of absolute/traversal paths, symlinks, hardlinks and special files across the entire archive.
- An 80 GiB unpacked-size cap, free-space check with 1 GiB reserve, and staging-directory extraction before rename.
- Interrupted extraction leaves staging only, not the final source directory.

The caps are operational limits for this approved single archive, not scientific sample thresholds. The host artifact volume reported 336,712,650,752 available bytes on 2026-09-22 (about 314 GiB). Earlier 2026-09-14 host and container-volume checks both reported about 249 GB available; these are time-specific observations.

Refreshed official `checksums.txt` and `LICENSE` into ignored `data/chembl37/` on 2026-09-22. The archive pin matches the approved SHA-256. The full archive acquisition has started through the tested downloader. At this log update it is **in progress**, not verified complete. No actual SQLite schema compatibility, chemistry results, assay decisions or feasibility conclusion is claimed.

Publication still needs broader failure/concurrency validation and exact complete-manifest/schema coverage before Phase 1 acceptance. Routine tests remain offline and synthetic. A reporter file is not evidence of automatic TDD write blocking.

### 2026-09-22 checkpoint while the archive transfers

Final checkpoint suite: **80 passed in 10.79s**. Additional red/green regressions cover missing/malformed manifests, concurrent identical publication (the losing caller verifies and compares the winner), and unlisted stored files. The concurrency test synchronizes the actual filesystem rename boundary; it does not replace serialization or integrity verification.

At 17:47 local time the archive partial file contained 571,473,920 bytes. The transfer was still active in Docker container `7cd404d75c01` (`trusting_borg`), not verified complete. Its approximate observed rate was below 1 MB/s, so a full transfer can take hours. The execution metadata snapshot is in ignored `data/chembl37/acquisition-2026-09-22-in-progress.json`; it is explicitly an in-progress record. Preserve the running container and partial file. The current downloader restarts an incomplete transfer on retry; it does not implement HTTP range resume.

Resume by inspecting the active container and final-versus-partial file state. A final filename alone is not acceptance evidence: recover the downloader exit/log result and verify the archive checksum. Then use the tested staged unpacker and perform the bounded actual-schema/target-slice check before completing source-dependent chemistry/profiling functionality. No source compatibility or scientific findings have been produced at this checkpoint.

### 2026-09-22 continuation during the same transfer

The existing downloader was preserved, not restarted. At 18:13 local time its partial file held 2,070,937,600 bytes (about 1.93 GiB). The process remained active at the final check; checksum verification and source-schema inspection are still pending.

Independent publication work continued through explicit red/green cycles. Added malformed artifact-metadata rejection and enforcement of the declared canonical byte contract for JSON and JSONL. Bare NaN and duplicate-key JSON payloads now fail publication instead of being labeled canonical. Nonfinite source values must go through the existing tagged serializer. The full offline checkpoint is **86 passed in 10.76s**. These remain synthetic engineering results, not evidence of source compatibility or scientific feasibility.

### 2026-09-23 — Interrupted acquisition recovery and independent chemistry

The September 22 original transfer ended with `SourceContractError: Source response truncated`.
Its unverified 4,715,359,725-byte partial was preserved as
`chembl_37_sqlite.tar.gz.failed-20260922.part`. A red/green regression then added
bounded full-restart recovery for truncation: the acquisition suite passed 21 cases.
No range-resume behavior was introduced. The replacement left a 36,700,160-byte
partial; on September 23 Docker was stopped and no container remained after restart.
The reason for that interruption is not established.

Started Docker Desktop and restarted the approved acquisition in named container
`assaytrace-chembl37-download-3`, retaining the container and its logs after exit.
The existing downloader replaces incomplete `.part` bytes on a full restart.
At 12:03 local time the current partial held 1,209,008,128 bytes. This is progress
only, not checksum verification. No archive extraction or actual-source schema
compatibility is claimed. The older in-progress JSON snapshot is historical.

Verified the carried-forward baseline: **87 passed in 14.67s**, offline.
While acquisition runs, started only source-independent Task 3 chemistry rules.
This ordering adjustment does not bring source-dependent adapters or scientific
profiling ahead of the required real-source check. Chemistry is not yet integrated
into the CLI and the complete Task 3 contract is not yet finished.

Each new chemical behavior was observed failing before minimal implementation:
atom-order invariance; exact listed-fragment removal with counts; organic-plus-
unlisted-sulfate ambiguity; a single remaining carbon-containing parent; removable
protonation versus permanent charge; explicit unsupported-structure dispositions;
separate stereo/tautomer measurement identities and equivalence keys; withheld
equivalence on actual limited enumeration; and ring/ACYCLIC scaffold outputs.
Chemical expectations and synthetic provenance are in `tests/fixtures/README.md`.
A misplaced assertion caused a NameError during charge-test verification; it was
corrected before the **102 passed in 15.07s** intermediate full regression run.
The enumerator setup was extracted with tests passing. Test-only enumeration
limits exercise real RDKit behavior; production remains capped at 1000.

The pytest TDD Guard reporter remains available. Automatic write-blocking
enforcement has not been established; red/green evidence is explicit.

Subsequent full checkpoints passed **112 tests in 15.41s** and **116 tests in
15.20s**. Added red/green coverage for enhanced/non-tetrahedral stereo rejection
and formal-charge reporting. Isotope/ordinary-hydrogen regression coverage passed
on first run against existing behavior; no new implementation or fictitious red
is claimed for that check.

Independent grouping red/green cycles cover deterministic structural-key groups,
unresolved-key exclusion, transitive union with scaffold links including ACYCLIC,
component quarantine for disagreeing, dangling, unresolved, multiple or cyclic
parent claims, valid self-parent claims and parent-only assignment exclusion.
The graph fixtures are abstract synthetic inputs. Full parent evidence auditing,
remaining boundary handling, reviewed-subset projection, chemistry audit/schema
completion and CLI integration remain unfinished. No real-source compatibility
or scientific acceptance follows from these tests.

The full offline suite then passed **125 tests in 15.85s**. At 12:33:45 local
time the third acquisition completed: 5,764,252,857 bytes, verified by the tested
streaming SHA-256 comparison against the approved pin before rename. Container
`assaytrace-chembl37-download-3` exited 0 and printed the final archive path.
Its log is retained; the external acquisition record is in ignored
`data/chembl37/acquisition-2026-09-23-complete.json`. Archive integrity is verified;
source schema compatibility and scientific feasibility are not yet established.

### First actual-source compatibility evidence

Staged extraction completed with exit 0 at `2026-09-23T19:57:50.619291869Z`.
The extracted SQLite file is 30,480,314,368 bytes; its final path is
`data/chembl37/extracted/chembl_37/chembl_37_sqlite/chembl_37.db`.
Schema evidence is preserved in ignored `data/chembl37/schema-inspection.json`.
The version table includes `ChEMBL_37` among several dependency entries; it is
not a single-row release table. The observed target is tid 93, CHEMBL220,
Acetylcholinesterase, SINGLE PROTEIN, Homo sapiens, tax_id 9606, with one component
357 / P22303 / homologue 0. The source reports its own RDKit 2022.09.4 dependency;
our profiling toolkit remains independently pinned and does not claim to reproduce
the source's original structure pipeline.

Two exploratory reads were interrupted by a 60-second query budget. The initial
plan started from all IC50 activities using `idx_act_std_type`, then checked
assays. A target-first rewrite still scanned the full assays table, which has no
tid index. Neither failed read produced accepted sample/count evidence. The
bounded compatibility query instead selects the first 20 target assays by
assay_id, follows `fk_act_assay_id`, and selects at most 20 IC50 records by
activity_id. It completed in 0.80 seconds. The query, parameters, plan and complete
sample payloads are in `data/chembl37/target-slice-inspection.json`; this is a
captured source slice, not a synthetic fixture or full candidate population.

The 20 sampled records reference assays 28147/28148. Both are type B but have
confidence 8, relationship H and null assay organism. Their descriptions mention
human AChE, but they fail the approved metadata screen. This is an observed
counterexample to target-only eligibility, not a full-target feasibility verdict
or a human-confirmed assay decision.

Added the bounded read-only adapter with explicit red/green cycles on authored
fixtures: target/endpoint/sample bounds, complete payload preservation, release
guard, positive integer limits and missing required-column errors. Release-row
presence does not independently authenticate a file; archive verification remains
the acquisition prerequisite. New source tests do not download data.

The opt-in actual-source check passed **1 test in 1.34s**, comparing the captured
activity IDs and all returned activity/assay fields against direct primary-key
reads and verifying target/component metadata. This is bounded adapter
compatibility evidence only. Full extraction, chemistry integration, grouping
audit completion, frozen review selection and scientific criteria remain pending.

Other interim work: missing/unknown completion-manifest versions now fail without
rewriting existing files; unresolved child equivalence retains parent links;
injected toolkit enumeration failure retains measurement identity and scaffold.
The latest full offline checkpoint before the adapter tests was **129 passed in
16.55s**. Source-compatibility success is reported separately from that checkpoint.

### 2026-09-24 — Synthetic chemistry/grouping integration

Further explicit red/green cycles added graph evidence edges, reviewed-subset
projection without broken bridges, and distinct source-molecule nodes when
measurement identities are absent. Atom/bond stereo-loss fault injection and
before/after normalization audit values also pass. Explicit `RemoveHs` was
introduced with existing isotope/stereo tests remaining green. The injected
failures are not claimed as observed ChEMBL or toolkit incidents.

After restarting Docker, the interrupted provenance test failed because the
specification lacked a chemistry contract. Settings now live in
`config/phase1-chemistry.json`, drive the wrapper, and appear in the profile with
the actual RDKit version and canonical digest. Existing chemistry tests stayed
green. Subsequent end-to-end red/green cycles added `molecules.jsonl` and
`groups.json`. Six synthetic activity records remain; records 1/2 share an
identity without collapse. Four exact numeric records include three with
resolved structures and two molecular identities. Missing structure is explicit.

Groups declare `synthetic_structure_only`, with source-parent and assay review
assessments `not_assessed`. They are not accepted real-source allocation groups
or a confirmed usable population. Full offline validation: **150 passed, 1 skipped
in 18.82s**. The skipped test is the separately exercised real-source check.
Immutable rerun/content-comparison and separate execution-record tests pass with
the additional artifacts. Automated TDD write blocking remains unverified.

### 2026-09-26 — Review selection, eligibility and resumable imports

Explicit red/green cycles established frozen high-coverage/stratified interleaving,
unknown year/format strata, metadata and selection digests, and duplicate assay
rejection. Local eligibility checks cover target and assay metadata, linked
human-confirmation state, numerical exclusions, structure resolution and record
contradictions. A regression exposed ignored metadata/group/record issues; these
now retain separate reason prefixes. Another exposed missing identifiers being
treated as matching. Group quarantine has separate allocation eligibility and
does not invalidate an otherwise eligible measurement. Exact-relation whitespace
is handled under the approved numerical contract.

Review snapshots preserve unvisited assays and assistant-proposed decisions.
Semantic content excludes reviewer attribution and timestamps. Integration tests
exercise immutable partial-import/resume, timestamp-only reuse with reconstructed
content comparison, altered-queue rejection, and invalid-budget rejection before
publication followed by a corrected retry. Active intervals count document time
inside the six-hour total; the 20-document and ten-minute-per-document caps are
checked. Overlapping, reversed and timezone-free intervals are rejected. An
evidence-linked early blocker is retained without deriving a scientific verdict.
The local `review-import` command is exercised through a subprocess.

Full offline checkpoint: **221 passed, 1 skipped in 18.52s**. A subsequent CLI
early-stop regression failed because the input stop was omitted; after correction,
all five review integration tests passed. These are authored synthetic cases, not
actual human confirmations, source compatibility evidence or feasibility results.
TDD Guard's reporter is available; automated write-blocking enforcement remains
unverified. Full candidate profiling, actual assay review and phase exit remain
unfinished.

### 2026-09-26 — Initial integrated scientific diagnostics

Further red/green cycles added source-record repeat counts and per-identity
dispersion, with missing assay/document provenance counted separately. Whole-group
allocation uses exact rational targets, seed-17 hash ordering for size ties, and
reports empty partitions without automatically failing scientific feasibility.
The source-warning contrast distinguishes record removal, disappearing identities,
unchanged shared medians and changed prospective medians. Unknown flags stay
separate. Held-out equivalence members cannot enter either prospective training
population; the common unflagged reference is explicitly restricted and is not
ground truth. Median outputs are labeled provisional what-if diagnostics.

An integration test retains quarantined measurements in descriptive outputs while
excluding them from allocation; duplicate extraction encounters go into the audit
without collapsing distinct source activity records. Criterion tests distinguish
prediction (population plus allocation) from the study (also curation), rejecting
incomplete or unconfirmed supported criteria. They do not supply a real scientific
verdict. Full offline suite: **243 passed, 1 skipped in 17.93s**.

These are initial component and integration checks, not completion of Tasks 4/5
or Phase 1. Remaining validation includes richer evidence/record-exception input
contracts, full-source wiring, actual review and criterion evidence, reproducible
real-profile publication, and phase acceptance. No modeling has been performed.

### 2026-09-26 — Full candidate source evidence and first review handoff

After additional red/green cycles, the full-target adapter preserves complete
activity payloads without a sample limit. Shared core release/schema validation
remains green in both bounded and full adapters. Recursive molecular-context
tests cover parent-only rows, self-parent claims, missing referenced molecules,
missing structures and absent/null mappings. Document extraction preserves null
years and missing references. The source-to-sampling integration counts distinct
source molecules without potency filtering. Review imports now preserve rationale,
missing evidence and document IDs in their semantic content; record exceptions
have evidence fields and apply to their linked activity.

Full offline verification: **266 passed, 1 skipped in 19.71s**. The separately
enabled actual-source check passed **1 test in 0.99s** after the adapter refactor.
Its bounded scope is unchanged; it is not independent validation of every row in
the full extraction. No automatic TDD write-blocking claim is made.

Actual read-only ChEMBL37 observations:

| Stage | Observed counts | Interpretation |
|---|---|---|
| Full target/IC50 extraction | 10,079 activity records; 8,372 source molecules; 1,031 assays with IC50 records | Uncurated candidate population. All 2,448 target assay metadata rows are also preserved. |
| Local B/9/D/human metadata screen | 7,214 activity records; 6,042 source molecules; 802 IC50 assays | Still not manually reviewed or numerically/chemically eligible. |
| Recursive molecule context | 9,490 rows; 1,118 auxiliary parents; 0 missing referenced molecule dictionary IDs | Parent-only nodes are not candidate observations. |
| Candidate measurement identity | 7,688 candidate molecule rows with identities; 7,668 distinct identities | 590 ambiguous-component, 39 missing-structure, 4 no-organic-parent and 51 unsupported-element candidate rows remain explicit. |
| Conservative grouping | 729 quarantined components; 190 affected candidate identities; 7,478 candidate identities grouped for allocation before review | Quarantine is not measurement invalidity. Component reasons: 553 parent-equivalence-unresolved, 173 parent-structure-unresolved, 3 parent-equivalence-conflict. |
| Pre-review grouping inventory | 7,274 equivalence groups; 3,167 scaffold-linked groups | These counts do not establish usable reviewed splits. |
| Frozen review selection | 60 high-coverage plus 60 stratified, deterministically interleaved | Missing document IDs in extracted context: 0. |

The chemistry run logged actual kekulization/tautomer-enumeration warnings;
unresolved chemistry is retained under the approved rules. No new normalization
policy or scientific threshold was introduced to increase coverage.

Source evidence is atomically stored under ignored `data/chembl37/` with manifests:
`candidate-extracts/e660b9a6...`, `molecule-contexts/95d096c1...`,
`candidate-chemistry/eef8e7f3...`, and `review-selections/951ffa85...`.
Separate execution records and retained Docker containers preserve run evidence.
This is a first full candidate reconstruction, not a claim of independent full
reconstruction on rerun or completed end-to-end acceptance.

[Batch 001](reviews/phase1-batch-001.md) presents ten evidence-linked proposals:
one assay-level compatible, one incompatible with the cell-free scope, eight
unresolved. All are still **assistant-proposed**. The immutable imported snapshot
is `review-state/reviews/4fdcbab9...`; it preserves 110 unreviewed entries and a
265-second conservative elapsed-session audit charge. No full texts were consulted
and no human-confirmed usable population or scientific exit verdict exists yet.
