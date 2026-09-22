# ExpertCheck 25.2 Alpha 2 — Evidence Admission Breakthrough

## Purpose

Alpha 1 proved that retrieval/executor coverage had increased sharply, but most
candidate evidence still died between retrieval and canonical proof. Alpha 2
targets that admission path directly.

## Changes

- Restores safe project-global binding for non-object requirements whose legacy
  scope is unresolved, without weakening object-specific owner gates.
- Resolves duplicate-id owner ambiguity when the executor already proves the
  exact requirement owner text.
- Repairs PDF line-wrap hyphenation before requirement/object classification.
- Prevents a secondary negative clause such as "не предусматривать" from
  reclassifying an otherwise positive engineering requirement as a prohibition.
- Allows a stronger generic presence proof to outrank a weaker concept-retrieval
  hit for the same requirement.
- Removes the impossible "minimum four terms" condition for short presence
  requirements: all available significant terms are sufficient when the other
  section, qualifier and design-assertion gates also pass.
- Adds per-requirement Core25 admission diagnostics:
  raw candidates -> verified candidates -> canonical/section-qualified evidence
  -> binding -> proof.
- Exposes binding reason-code counts in the technical report.
- Shows the actual runtime version on the Assignment UI instead of a hard-coded
  25.0 label.

## Safety / proof policy

Alpha 2 does not promote ordinary candidates to categorical results. A result
still requires verified, addressable, canonical evidence and a valid Core25
binding/proof trace. Object-specific owner and parameter conflicts remain
fail-closed.

## Automated validation

Validated HEAD: `9a2fc0091b6c06c71524e6d21abb8338adf46659`

- Core25: **89 passed / 0 failed**
- Core20 regression: **95 passed / 0 failed**
- Core20 main: **95 passed / 0 failed**
- Results/report integrity: **17 passed / 0 failed**
- Full release gate: **530 passed / 32 classified historical failures / 0 blockers**
- Historical failure classes: **3 fixture-bound / 4 obsolete / 25 baseline-existing**
- Core25 compile/release gate: **SUCCESS**

## Manual benchmark

Status: **READY_FOR_FRESH_TEST78_BASELINE**

Run on a new project from the same 12-file Test 78 package. Do not run an
additional AI pass before recording the deterministic Assignment baseline.

Primary benchmark:
- 25.0: 2 / 56
- 25.1: 2 / 56
- 25.2 Alpha 1: 5 / 56
- 25.2 Alpha 2: to be measured

The first review target is not merely the final 56-row count. The new technical
report must also show where every non-categorical requirement stopped in the
admission chain.
