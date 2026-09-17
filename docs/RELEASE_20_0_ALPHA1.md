# ExpertCheck 20.0 Alpha 1 · Canonical Engineering Core · Dual Run

## Scope

Alpha 1 establishes the migration foundation for the 20.0 major release.

Implemented:

- isolated `core20` package;
- canonical entities and reference validation;
- stable canonical IDs;
- compact one-way `Legacy18Adapter`;
- formal Test 77 18.7.3 baseline;
- three golden engineering cases;
- baseline and golden-case parity gates;
- observational dual-run manifest in Studio;
- developer-mode telemetry for canonical objects/properties/evidence and migration errors;
- regression tests for broken references, baseline loss, 36/3 object scope behavior and 23.5/89.9 binding separation.

## Safety contract

20.0 Alpha 1 does not change any legacy result. The Studio explicitly marks `legacy_results_unchanged=True` in the dual-run manifest.

## Expected first control test

Open the existing PostgreSQL `Тест 77`; do not upload PDFs and do not run AI.

In developer mode open `20.0 · Canonical Core` in the sidebar.

Expected:

- no canonical migration exception;
- zero broken-reference ERRORs;
- canonical candidate/object counts reflect the confirmed object assembly;
- properties and evidence are non-zero;
- golden cases should move toward `OK`; if a golden case is missing because legacy source rows are not present in the restored public collections, that is a migration gap to fix before Verification Engine 2.0 replaces anything.

## Next milestone

`20.0 Alpha 2 — Verification Engine 2.0 Foundation`

Alpha 2 will introduce typed verification contracts over canonical state while legacy 18.7.3 continues to provide the authoritative verdict for comparison.
