# Synthetic fixtures

All fixtures currently in this repository are authored synthetic examples.
They are not captured ChEMBL records or evidence of source compatibility.
The SQLite schema in `tests/conftest.py` is deliberately minimal. Its six
activity records include two distinct equal-valued IC50 records, one Ki,
one censored IC50 and one exact IC50 lacking a structure. Four records have
exact numerical IC50 values, but that count does not imply scientific eligibility.
Two component links exercise the risk of multiplying activity rows through joins.

The fixture values and schema are released under CC0-1.0 for redistribution.

Chemistry fixtures are authored molecular examples, not extracted measurements.
`CCO` and `OCC` describe ethanol with opposite atom traversal orders; changing
that traversal must not change its measurement identity.
Ethanol plus benzene has two organic components; ethanol plus sulfate has one
organic and one unlisted inorganic component. Both must remain ambiguous under
the approved exact-fragment policy; neither permits largest-fragment selection.
Ethanol accompanied by two copies of each explicitly listed removable fragment
must retain ethanol and report both removed copies. These are policy-boundary
examples, not claims that every mixture is an experimentally plausible salt.
After listed fragments are removed, no component means no parent; sulfate alone
cannot supply a carbon-containing parent. Methylammonium has a removable proton
and should match methylamine after neutralization. Tetramethylammonium has four
carbon bonds at nitrogen; its permanent positive charge must remain.
Opposite lactic-acid stereoisomers have distinct measurement identities but must
share the conservative stereochemistry-free equivalence key. Unspecified stereo
does not establish a racemate. Empty, malformed, dummy-atom, radical and silicon
examples exercise explicit exclusions from the approved chemistry scope.
Acetone and its enol differ in hydrogen and double-bond placement. Their retained
measurement parents remain distinct, while completed tautomer enumeration must
link them conservatively for allocation.
Toluene and ethylbenzene both have a benzene ring framework after side chains
are removed; ethanol is acyclic. The limit test uses the real RDKit enumerator
with a test-only cap of one tautomer to exercise incomplete enumeration. It does
not replace the production cap of 1000 or manufacture an enumeration response.

The isotope examples distinguish deuterated and carbon-13 methanol from
unlabelled methanol while ordinary explicit hydrogen does not change identity.
Enhanced AND stereo and trigonal-bipyramidal phosphorus exercise unsupported
stereo exclusions. These examples do not assert bioactivity or source prevalence.

Grouping fixtures use abstract identity/equivalence/scaffold labels to isolate
graph behavior. They test transitive unions, absent versus dangling references,
conflicting and multiple parent claims, non-self cycles versus valid self-parent
claims, and exclusion of parent-only nodes from observation assignments. These
are authored graph contracts, not captured ChEMBL hierarchy records.

`test_release_slice.py` contains a second authored SQLite fixture informed by the
observed ChEMBL table/column names. Its identifiers, measurements and version
entries are test data and do not authenticate a release. The opt-in
`tests/source/test_chembl37_contract.py` instead reads the user's verified local
archive database and checks actual captured activity IDs against independent
primary-key reads. It is skipped unless explicitly enabled. Passing that check
establishes compatibility for the bounded slice, not scientific eligibility.

`test_candidate_profile.py` composes authored source-shaped bundles, molecular
examples and review snapshots. Its `human_confirmed` labels are synthetic test
inputs, never real assay approvals. The tests exercise local provenance links,
record exclusions, grouping quarantine, unknown review state, deterministic
reconstruction and publication recovery. Their success is not ChEMBL source
compatibility or scientific feasibility evidence.
