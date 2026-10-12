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

### 2026-10-10 to 2026-10-11 — Stored-input profile integration and recovery

Resumed the interrupted reader test from the actual workspace: its stub and test
were present, and the first observed run failed at `assert result is not None`.
The shell sandbox initially failed before process startup (`setup refresh had
errors`); the authorized elevated route restored access. The approval-review
service later hit a usage limit before the evidence-log update executed. On the
next continuation, Docker Desktop was restarted and saved results were verified.
No new dependencies, archive downloads, models or services were introduced.

The user explicitly deferred batch 001 review: all ten decisions stay
assistant-proposed. Neither the source ledger nor its immutable snapshot changed.

Ruling: retain this execution ledger and the approved inline workflow rather than
introducing a second bookkeeping tree — continuity with Windows/Docker execution
— the cost is manual rather than helper-enforced progress tracking.

Ruling: implement the plan's local `profile` interface with `--inputs` referencing
four stored manifests — compose preserved source evidence with the scientific
functions without repeating extraction — this proves reconstruction from stored
inputs only. Independent archive extraction remains an acceptance obligation.

Tests used the existing image without network:

```powershell
& "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe" run --rm --network none --mount "type=bind,source=$PWD,target=/workspace" -w /workspace assaytrace-phase1:test python -m pytest tests/unit/test_bundle_reading.py -q
& "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe" run --rm --network none --mount "type=bind,source=$PWD,target=/workspace" -w /workspace assaytrace-phase1:test python -m pytest tests/integration/test_candidate_profile.py -q
```

Each new behavior was introduced separately; parameterized cases exercise the
same contract. Observed red/green cycles:

| Behavior | Observed red | Subsequent green |
|---|---|---|
| Read immutable bundle without claiming reconstruction | Stub returned `None` | 1 reader test |
| Verify stored bytes and hash/count metadata | Six corruptions accepted | 7 reader tests; 41 including publication |
| Reject malformed/incomplete manifests and inventory | Eleven cases accepted or errors unclassified | 18 reader tests; 52 including publication |
| Enforce canonical bytes with a matching file hash | Two noncanonical payloads accepted; malformed JSON unclassified | 21 reader tests; 55 including publication |
| Compose source records, chemistry, review and diagnostics | Profile stub returned `None` | 1 candidate integration test |
| Preserve numeric exclusions without aborting or converting Ki | Four exclusion cases failed | 5 candidate tests |
| Retain parent-conflicted measurements outside allocation | Quarantined identity reached allocation | 6 candidate tests; 38 including eligibility/evidence |
| Deduplicate extraction encounters and sort published rows | Activity IDs were `[2,1,1]` | 7 candidate tests |
| Wire `profile --inputs` with reconstruction comparison | CLI rejected missing `--source` | 8 candidate tests; 19 including original CLI |
| Reject intact but incoherent input bundles | Nine provenance/scope mismatches accepted | 17 candidate tests; 28 including original CLI |
| Keep synthetic inputs explicitly synthetic | Unlabelled synthetic data published as release input | 18 candidate tests |
| Report unconfirmed/unreviewed populations | Two cases lacked eligible-population counts | 20 candidate tests; 31 including original CLI |

With passing tests, publication was refactored to share stored-integrity checks,
and both CLI paths share processing/environment provenance. Incoming-content
comparison remains mandatory. Two additional integration tests exercise artifact
write failure and lost acknowledgment after publication. Both passed with existing
recovery behavior; no new production red/green cycle is claimed for them.
Candidate integration suite: **22 passed in 2.43s**.

The full offline command used the same Docker prefix with `python -m pytest -q`:
**309 passed, 1 skipped in 22.01s**, exit 0. The skipped test is the opt-in source
adapter test; it was not rerun because the adapter did not change. The reporter
updated `.claude/tdd-guard/data/test.json`; automated write blocking remains
unverified. Synthetic success is not source compatibility or scientific evidence.

All five existing source/review/chemistry bundles passed `read_bundle` verification
using a read-only mount. The real CLI used `config/phase1.json`, no network, a
four-CPU cap and 4 GiB memory cap. Retained container
`assaytrace-reviewed-profile-20261010` exited 0, running from
`2026-10-11T01:44:20.01678691Z` to `2026-10-11T01:46:23.220615889Z`
(October 10 locally). One in-run sample showed 99.68% CPU and 237.4 MiB memory;
this is not a peak measurement. Chemistry warnings remain in the container log.
No normalization policy was relaxed to suppress unresolved structures.

The resulting profile ID is
`c210854c12fff687fe1127124650f0e00708d344d27b49c0e3f5d45bc3cbf7af`,
under `data/chembl37/reviewed-profiles/profiles/`. Manifest SHA-256:
`03ad9102561998f1afb06a4afcf514165eb5f8142f68c91728a028a819baa05e`.
It retains **10,079 source records**, **10 proposed assay decisions**, **110
unreviewed selected assays**, **0 human confirmations**, and **0 eligible reviewed
measurements/allocations**. Zero eligible counts reflect pending review, not
scientific failure. `scientific_assessment` remains `not_performed`.

Two full stored-input reconstructions then completed:

| Container | Output scope | UTC start / finish | Exit |
|---|---|---|---|
| `assaytrace-reviewed-rerun-20261010` | Existing profile directory | 01:46:59.733341022 / 01:49:01.702244507 on October 11 | 0 |
| `assaytrace-reviewed-validation-20261010` | Separate `data/chembl37/reviewed-profiles-validation` | 01:46:59.972192563 / 01:49:01.821060045 on October 11 | 0 |

Both produced the same profile and manifest hashes. The first records
`reused: true`, `validation_mode: reconstruction_compared`; the second published
a new directory. On October 11, an independent PowerShell SHA-256 comparison
verified all six files (`activities.jsonl`, `molecules.jsonl`, `groups.json`,
`evidence.json`, `summary.json`, `manifest.json`) against the pre-rerun inventory
and the separate reconstruction. Original last-write ticks also remained equal.
These checks reconstruct from saved extraction artifacts, not from SQLite/archive.
The shared reader also verified both completed bundles on October 11. Their
activity output has exactly 10,079 unique release-qualified keys. Recomputed
`molecules.jsonl` and `groups.json` match the September 26 chemistry checkpoint
byte-for-byte, providing a further comparison against the earlier execution.

Phase 1 remains incomplete: human assay review and scientific criteria, independent
source re-extraction, fuller relationship/evidence contracts, acquisition and
assessment CLI wiring, and accurate start/end/failure run audits remain pending.

### 2026-10-11 — Execution timing and publication-failure audit correction

Saved the verified stored-input profile integration in local commit `654fc70`.
The next approved operational step corrects a real audit limitation: `record_run`
previously overwrote execution start with the time it wrote the acknowledgment.

Using the same offline Docker test prefix:

| Behavior | Observed red | Green |
|---|---|---|
| Separate execution timing from acknowledgment | Both unspecified and supplied timing cases received an invented/overwritten start | `test_publication.py`: 36 passed in 1.30s |
| Capture actual processing boundaries for candidate profile, synthetic profile and review import | Three CLI run records had null start times | Candidate/publication/review-resume suites: 66 passed in 7.28s |
| Record a failed run without a completion manifest | Audit attempted to hash a nonexistent manifest | Publication suite: 37 passed in 1.27s |
| Preserve a failed candidate publication attempt through retry | No failed-run record existed after an injected artifact-write failure | Candidate/publication suites: 62 passed in 6.44s |

Execution start/finish remain outside scientific artifacts. `recorded_at` denotes
acknowledgment time. Unspecified timing in direct helper calls remains null rather
than fabricated. Existing historical records are untouched. Candidate publication
failures now retain an intended profile ID and error type/message without a
completion-manifest claim, when the run directory is writable. Lost-acknowledgment
recovery still verifies the completed bundle; a failed audit write cannot guarantee
a run record. Pre-publication computation/input failures and failure audit wiring
for other CLI commands remain pending, as documented in the data dictionary.

Full offline verification: `python -m pytest -q` in the reference Docker image,
**315 passed, 1 skipped in 29.13s**, exit 0. The skipped source test remains opt-in;
no source-adapter changes were made. `git diff --check` passed. The real timing
validation is recorded below after its result is inspected.

Real validation completed successfully in retained container
`assaytrace-audited-profile-20261011` (exit 0). Its new profile is
`data/chembl37/audited-profiles/profiles/f92d78e8921655cc1d6547e4891cad01cb2182e36757fc03c94da5b7552a0abc/`;
manifest SHA-256 is
`79f481c47415aed061e487bd05db78efbf9c949fd45f6d7eff9561598262739c`.
Read-only verification confirms all five scientific artifacts are byte-identical
to the preceding profile. Only `processing_code_sha256` differs in the
specification, appropriately producing a new profile identity.

The run audit at `data/chembl37/audited-profiles/runs/d882d2d5d6f44a829447d8fc44306267.json`
records UTC start `2026-10-11T16:24:05.166002+00:00`, finish
`2026-10-11T16:26:37.926015+00:00` and acknowledgment
`2026-10-11T16:26:37.931689+00:00`: **152.760013 seconds** of measured execution.
All three fall within Docker's independently recorded container start/finish,
in the correct order. No source or review state changed. The
[interim findings](phase1-findings.md) summarize the unresolved scientific criteria;
they are not a phase-exit acceptance request.

### 2026-10-11 — Independent pinned-source reconstruction acceptance check

Started retained container `assaytrace-source-reconstruction-20261011` with no
network, four-CPU/4-GiB caps, a read-only workspace mount and a separate writable
`data/chembl37/source-validation` evidence directory. Available host disk space
before starting was 221,943,906,304 bytes. The one-off verification driver is
preserved at `artifacts/validation/source_reconstruction_20261011.py`; it calls
the tested adapters and publisher rather than introducing new scientific rules.

The check streams the archive checksum and its SQLite member, compares the local
database bytes, then independently re-extracts the target activities, recursive
molecular context, preserved document-ID request, sampling rows and frozen queue.
It does not download data or write another 30-GB database copy. Each reconstructed
artifact must match its prior counterpart before a verification bundle can be
published. Results are recorded below only after completion.

During this acceptance work the separate real-source adapter command was rerun:
`python -m pytest tests/source/test_chembl37_contract.py -q` with
`ASSAYTRACE_CHEMBL37_SQLITE=/workspace/data/chembl37/extracted/chembl_37/chembl_37_sqlite/chembl_37.db`
inside the existing Docker image. **1 passed in 1.13s**, exit 0. This remains a
bounded actual-source check, distinct from 315 passing offline tests and from
scientific review. The new root README's local links all resolved; documentation
status now reflects approved, ongoing Phase 1 execution without advancing phases.

The retained container finished with exit 0 at `2026-10-11T16:46:24.546880691Z`
(start `2026-10-11T16:30:53.808051769Z`). Its completed verification bundle is
`data/chembl37/source-validation/bundles/7a33c64c89d21da15d729cb0d1e77c1f7c5d4bf1995734126a1164fd7b56c4c8/`.
Manifest SHA-256:
`85ad7f031c19e53c96c680b9abe211de6409bba3a7182089c170bbc8c06ebb18`.
The separately recorded execution ran from `16:30:54.894198+00:00` to
`16:46:24.450491+00:00`; acknowledgment followed at `16:46:24.453307+00:00`.

- Archive SHA-256 matches the approved pin:
  `33c203740555f96067710cdfc1c3c55d890660e5908ec5cbf5817492c290d281`.
- The local 30,480,314,368-byte database matches member
  `chembl_37/chembl_37_sqlite/chembl_37.db`, SHA-256
  `4be13df3b68e25dcd0bff44bf094033b5aebe98f415acdc8c1cdf380e0c15142`.
- Fresh canonical outputs match the preserved artifacts byte-for-byte: 10,079
  activities, 9,490 molecular-context rows, 881 documents, sampling rows and the
  frozen 120-assay queue. Documents were requested using the same IDs as the
  preserved context; this is not a completeness claim for other document scopes.

This was a separate reconstruction using the same production adapters, not an
independent implementation of their scientific interpretation. No review state
changed, no models ran and scientific assessment remains `not_performed`.

### 2026-10-11 — Review-exception source linkage

The approved record-level contradiction rule requires an exception to identify
an activity in the reviewed assay. Added one parameterized integration test for
a wrong-assay activity and an absent activity. Before implementation,
`python -m pytest tests/integration/test_candidate_profile.py -q --tb=short`
produced **2 failed, 25 passed in 3.77s**, exit 1; both failed because the pipeline
did not raise. The minimal fix checks the activity/assay links before profiling.
Then `python -m pytest tests/integration/test_candidate_profile.py tests/unit/test_review_eligibility.py -q --tb=short`
produced **57 passed in 3.54s**, exit 0. No refactoring was needed for this small
validation. Explicit TDD was observed; automated TDD Guard write-blocking
enforcement remains unverified. All real batch 001 exception lists remain empty.

Full offline regression after this change: `python -m pytest -q` in the reference
Docker image with networking disabled: **317 passed, 1 skipped in 23.47s**, exit 0.
The skipped live-source test is separately recorded above. This run does not
alter the still-unconfirmed scientific assessment.

### 2026-10-11 — Explicit criterion-assessment CLI

Implemented the approved local `assess` interface from Tasks 5–6. Routine
interface choices: `--profile` names a completed unassessed candidate manifest;
`--ledger` carries its exact manifest digest, the three criteria and narrative;
`--output` receives a new immutable profile. `--synthetic` is mandatory for
synthetic source identity. Evidence references name artifacts in that bound
profile; arbitrary external evidence resolution is not implemented here.
These choices add no scientific threshold, automatic verdict or review authority.

Observed red–green cycles used
`python -m pytest tests/integration/test_candidate_profile.py -k <selector> -q --tb=short`
inside the existing Docker image with networking disabled:

| Behavior / selector | Observed red | Minimal green evidence |
|---|---|---|
| `assess_cli` initial explicit ledger publication | 1 failed: command returned parser status 2, not 0 | Candidate plus criterion tests: 42 passed in 2.61s |
| `ledger_bound` exact evidence-profile digest | 1 failed: wrong digest did not raise | Assessment subset: 2 passed in 1.20s |
| `assess_cli_rejects_source` source mode | 3 failed: mode mismatches did not raise | Assessment subset: 5 passed in 1.45s |
| `malformed_evidence` semantic fields and resolvable references | 7 failed: malformed/unresolved inputs did not raise | Candidate plus criterion tests: 53 passed in 5.04s |
| `requires_a_complete` candidate profile contract | 2 failed: incompatible profile contracts did not raise | Assessment subset: 14 passed in 2.64s |
| `assess_cli_audits` publication failure | 1 failed: expected one failed-run record, found zero | Candidate integration file: 42 passed in 4.72s |

After green, extracted shared source-mode validation and publication/failure
auditing used by candidate and assessment paths. Candidate plus criterion tests
remained green: **57 passed in 5.75s**. An added integration check of existing
rerun/amendment behavior passed immediately (1 passed in 1.31s); it is supplemental
coverage, not a claimed new red–green cycle. Two further integration cases exercise
the existing prohibition on unconfirmed supported/not-supported criteria.

Full final offline command: `python -m pytest -q`, reference Docker image,
networking disabled: **335 passed, 1 skipped in 25.52s**, exit 0. The opt-in source
test is the skip; its separately observed result is recorded above. Automated
TDD Guard write-blocking enforcement remains unverified; explicit TDD was used.

The real-data invocation documented in [operations](phase1-operations.md) returned
exit 0 using [the interim ledger](reviews/phase1-interim-criteria.json). It derived
`data/chembl37/interim-assessments/profiles/e46d285b8ed888e5b5ca0b2b15b208dcfbcd6bcd90a655b0fe170354f9cf47c8/`
from the earlier `f92d78e8...` evidence profile. Derived manifest SHA-256:
`193e4a351953c805881454be1875404030e029b6b689df47dc1faf5944a8511f`.

A second invocation through the same CLI entry point returned `reused=true` and
`validation_mode=reconstruction_compared`. Independent checks confirmed:

- All derived bundle file hashes and modification timestamps remained unchanged.
- Activities, molecules, groups and diagnostic evidence match the source profile
  byte-for-byte. Only the summary's `scientific_assessment` field changes to
  `assistant_proposed`, and `assessment.json` is added.
- Counts remain 10,079 activities, 10 proposed assay decisions, 110 unreviewed
  selected assays, zero confirmed assays and zero eligible reviewed records.
- Prediction and study conclusions are both `inconclusive`, with all three
  criteria explicitly assistant-proposed. No assay decision was changed.
- The earlier source-verification bundle also passed a fresh `read_bundle`
  integrity check (`stored_integrity_only`); the large archive was not rehashed.

Assessment reconstruction validates this composition and explicit input contract.
It does not rerun chemistry or establish the scientific truth of the supplied
criterion narratives. Human review, acquisition CLI wiring, broader error audits,
remaining source/evidence checks and phase acceptance are still outstanding.

### 2026-10-12 UTC — User confirmation of assay 2351073

The user explicitly selected "1. Confirm compatible at assay level" after the
single-assay walkthrough. The [confirmation record](reviews/phase1-batch-001-confirmations.md)
preserves that scope and the limitation that full methods/supporting information
have not been independently checked. This is October 11 in the user's timezone.

Published the updated local ledger
`data/chembl37/review-ledgers/batch-001-confirmed-2351073.json` using the existing
`publish_reviews` function in the reference Docker image with networking disabled.
The command completed with exit 0 and published review snapshot
`21ef698d86b28d9060dc527d345fd2ab536a2617b29acef8ddb0a636ac658f78`.
Run record: `data/chembl37/review-state/runs/62a8207fff164947893e1c7b8f6d7ce6.json`.

Direct assertions and `read_bundle` verification confirmed exactly one
human-confirmed assay (2351073), nine assistant-proposed decisions, 110 unreviewed
selected assays, unchanged frozen selection bytes and unchanged original snapshot
file hashes/timestamps. The other nine input decisions were compared unchanged
against the original ledger. The updated confirmed decision retains source
evidence references and adds the content hash of the confirmation note.

`config/phase1.json` now points to the new review manifest. Existing profiles and
interim assessments remain preserved; they have not been recomputed. No usable
record count or revised criterion verdict follows from this administrative update.
No application code changed, so a new red–green cycle or full test-suite rerun was
not needed. This entry records actual import/integrity checks, not a new test count.

### 2026-10-12 UTC — User confirms assay 902584 as unresolved

The user selected "1. Confirm unresolved" after the single-assay explanation.
The [separate confirmation note](reviews/phase1-batch-001-confirmation-902584.md)
preserves the evidence gap and explicit distinction between confirming a
disposition and approving eligibility. The earlier hashed confirmation note for
2351073 was not edited.

The existing `publish_reviews` function completed with exit 0 in the reference
Docker image, networking disabled. It imported
`data/chembl37/review-ledgers/batch-001-confirmed-2351073-902584.json` and produced
review snapshot `d5bcdef7b33e1a0fb0b92446f6010c5117904966f3770a41f1e3902567d06aa5`.
Run record: `data/chembl37/review-state/runs/de631a03e05e4c22b475d0e2d686d40c.json`.

Assertions and `read_bundle` verified confirmed dispositions exactly
`{902584: unresolved, 2351073: compatible}`, eight assistant proposals and 110
unreviewed selected assays. All other input decisions, frozen selection bytes,
and prior snapshot hashes/modification times were preserved. The active descriptor
now points to the new snapshot. No application code changed or profiling ran;
existing scientific counts and criterion assessments remain historical.
