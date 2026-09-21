# ExpertCheck 25.0 Alpha 1 — release validation

Validated branch: `codex/expertcheck-25.0-quality-leap`  
Validated code HEAD: `cfde609b4adc09d592a4e9a69302c8ebd4e4dea3`

## Status

**Release gate: NOT_READY_FOR_MANUAL_TEST**

The Alpha 1 Unified Verification Core satisfies all ten acceptance gates from the approved 25.0 design specification.

## Fresh verification evidence

- Core25 suite: **64 passed / 0 failed**.
- Core20 regression suite: **95 passed / 0 failed**.
- Mandatory focused evidence/provenance regressions: **14 passed / 0 failed**.
- Core25 compile check: **PASS**.
- Control Assignment gate routes **56/56 requirements** through the 25.0 pipeline.

## Historical repository diagnostics

The broad historical repository suite still contains **32 failed nodeids**, but the exact same set was reproduced on the stable baseline `6afaf020f329f07bdbce6d0ea2c0e1238023aed6`.

Classification:

- **3** external-fixture-bound;
- **4** obsolete release-version assertions;
- **25** baseline-existing behavioral diagnostics;
- **0** unclassified/current-branch blockers.

The Alpha 1 workflow is now fail-closed: any failed nodeid outside this exact classified baseline set fails the release gate.

## Final integrity hardening

The final self-review added regression-backed guards so that:

- TOC/index evidence is rejected if either its source kind or source role identifies it as non-proof evidence;
- a categorical Decision cannot carry a `proof_id` different from its concrete `Proof25`;
- every evidence item claimed by a categorical proof must have a matching BOUND binding;
- trace requirement identity must remain consistent through proof and decision;
- report export and persistence reload reject forged cross-owner or wrong-parameter categorical traces.

## Core20 ruling

One small change remains in `core20/evidence_quality_1012.py`. It is not 25.0 verdict logic. The stable baseline implementation has an order-dependent behavior: its own focused Alpha 10.1.2 evidence-quality regression fails when run in isolation. The retained topic-alignment fix makes that pre-existing regression deterministic. It is separately covered by Core20 regression and focused release-gate tests.

## Manual validation

The automated Alpha 1 release gate is complete. The next useful step is the planned user-level manual control run (Test 78 / control package) against the 25.0 Alpha 1 build. Do not merge the draft PR into the stable 20.0 branch until that manual control run has been reviewed.


## Runtime integration blocker discovered during first user launch

The startup `AttributeError` on the «Мои проекты» page was traced to an incomplete `StudioContext ↔ WorkspaceStore` contract. The branch now passes `workspace_store` explicitly and uses the correct explicit `save_project` autosave signature.

The same investigation exposed a more important release gap: the Streamlit application currently imports and runs the existing `core/pipeline.py` path and does **not** invoke `core25.verify_assignment`. The visible application version is still 20.0 Alpha 10.1.3. Therefore a user-level Test 78 run at this point would test the old runtime, not the new 25.0 Unified Verification Core.

Manual validation is paused until the 25.0 runtime bridge is implemented, covered by integration tests, and the application visibly identifies the 25.0 Alpha 1 build.


## Runtime bridge completed

The application now executes `core25.runtime_bridge.run_assignment_runtime()` from the real `core/pipeline.py` Assignment stage after deterministic directed-evidence retrieval. Core25 independently performs Routing → Evidence qualification → Binding → Proof → Decision; the legacy status is not reused as the Core25 verdict.

Public Assignment surfaces now select `assignment_core25_*` through `public_assignment_payload()`:

- Project / «Задание на проектирование»;
- Results Center;
- generated XLSX reports.

If the Core25 runtime fails, new analyses fail closed on the Core25 surface instead of silently falling back to the legacy verdict. Legacy snapshots created before 25.0 remain readable.

The first Streamlit launch also exposed and fixed the separate `StudioContext.workspace_store` startup defect and the autosave `save_project` argument mismatch.

### Current automated validation

At code HEAD `300593c2372a08f2999dc63f57afbe884975d67b`:

- Core25: **73 passed / 0 failed**;
- Core20 regression: **95 passed / 0 failed**;
- mandatory focused regressions: **14 passed / 0 failed**;
- Alpha 1 release gate: **SUCCESS**;
- historical diagnostics: **32 classified / 0 blockers**.

**Manual release status: READY_FOR_MANUAL_TEST.**

The next step is a fresh Test 78 run from a new analysis on the 25.0 Alpha 1 Runtime Bridge build. Existing saved analyses from older builds should not be used to judge Core25 behavior.
