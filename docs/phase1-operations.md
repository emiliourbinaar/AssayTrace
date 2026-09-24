# Phase 1 operations — in development

The current CLI supports the authored synthetic fixture only. The pinned ChEMBL
archive has been verified and extracted, and a bounded source adapter check has
passed. The synthetic CLI now publishes molecular identities and provisional
structure groups as well as numerical results. Full real-source extraction,
parent-mapping integration and human assay review remain incomplete.

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
