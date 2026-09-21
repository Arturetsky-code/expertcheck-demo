# ExpertCheck 25.0 Alpha 1 — validation status

Validated branch: `codex/expertcheck-25.0-quality-leap`  
Validated commit: `08bdf47a60ccb369c9d97aec052c715699ff0bba`

## Current status

**Release gate: NOT_READY**

The active 25.0 verification core is green, but the repository-wide historical diagnostic suite still contains failures that have not yet been fully classified against the Alpha 1 release contract. Alpha 1 must not be presented as release-ready until that classification is complete.

## Proven green gates

- Core25 suite: **53 passed / 0 failed**.
- Active Core20 regression suite: **95 passed / 0 failed**.
- Mandatory focused evidence/provenance regressions: **14 passed / 0 failed**.
- Core25 compile check: **PASS**.
- Control Assignment test covers **56 requirements** through the 25.0 pipeline.
- Categorical decisions require canonical addressable evidence and valid proof trace.
- Wrong-owner binding cannot become a categorical mismatch.
- TOC/index-only evidence cannot satisfy proof.
- Persistence round-trip preserves canonical evidence/binding/proof trace.
- Public report mapping fails closed for an invalid categorical trace.
- Test 78 Golden Set is automated.

## Remaining release blocker

The full historical repository diagnostic run currently reports:

- **494 passed**
- **32 failed**

These failures include old mutually incompatible release expectations and tests requiring external `/mnt/data` fixtures, but the set also contains behavioral failures. They must be classified one by one into:

1. historical/obsolete release contract;
2. unavailable external fixture;
3. real regression relevant to the current 20.0/25.0 supported contract.

Only category 3 blocks the product and must be fixed. Categories 1–2 must be explicitly documented, not silently hidden.

## Next action

Classify all 32 diagnostic failures, add a machine-readable allowlist only for demonstrably obsolete/fixture-bound diagnostics, and re-run the Alpha 1 release gate. The build becomes `READY` only when there are zero unclassified or current-contract failures.
