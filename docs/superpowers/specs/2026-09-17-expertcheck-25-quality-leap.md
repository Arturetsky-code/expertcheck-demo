# ExpertCheck 25.0 · Quality Leap — Architecture Spec

## Status
Approved by product owner on 2026-09-17.

## Goal
Deliver a measurable quality jump by replacing duplicated verification flows with one strict verification pipeline shared by Design Assignment, normative checks, checklist automation, and inter-section comparison.

## Architecture choice
Use a new `core25` package alongside stable `core20`.

Do not rewrite the application from scratch. Reuse proven `core20` mechanisms through explicit adapters, while all new verdict-producing flows pass through `core25` contracts and integrity gates.

## Canonical pipeline

`Requirement -> Route -> Evidence -> Binding -> Proof -> Decision -> Trace`

No subsystem may bypass this pipeline when producing categorical results.

## Core invariant

**No proven Binding -> no Proof -> no categorical Verdict.**

`COMPLIANT` and `NONCOMPLIANT` are forbidden unless all required proof preconditions are satisfied.

## Domain model

### Requirement
Represents one atomic requirement. Must contain:
- stable requirement id;
- source domain;
- original text;
- normalized atomic condition;
- verification kind;
- target scope/object when known;
- expected parameter or engineering decision when known;
- expected evidence route;
- required proof slots.

### Evidence
Represents one addressable source fragment. Must contain:
- stable evidence id;
- document identity;
- section/document role;
- page;
- fragment;
- source kind;
- addressability state;
- trust/provenance metadata.

A table of contents, generic search hit, AI summary, or unaddressable fragment cannot independently satisfy proof.

### Binding
Represents the demonstrated semantic ownership of Evidence:
- project object;
- parameter / engineering decision;
- value and unit when applicable;
- source evidence;
- binding basis;
- binding state;
- confidence is diagnostic only and is never proof by itself.

Binding must distinguish semantically different owners even when numeric values or nearby words look similar.

### Proof
Represents the verified relation between one Requirement and one or more Bindings/Evidence items. Proof is valid only when required proof slots are fulfilled.

### Decision
Allowed terminal states:
- `COMPLIANT`;
- `NONCOMPLIANT`;
- `REVIEW`;
- `LIMITATION`.

`REVIEW` and `LIMITATION` are valid outcomes and must be preferred over unsupported certainty.

## AI role
AI may:
- atomize text;
- classify requirement type;
- propose routes;
- retrieve and rank evidence candidates;
- propose object/parameter bindings;
- act as Judge/Critic.

AI may not independently create a categorical verdict. Deterministic integrity gates remain authoritative.

## Alpha 1 scope
The first vertical slice is Design Assignment verification.

The existing DSK regression fixture contains 56 atomic requirements. Alpha 1 must route every requirement through the new pipeline. Not every requirement must be automatically decided; unsupported cases must end as `REVIEW` or `LIMITATION`.

## Alpha 1 acceptance gate
Alpha 1 is not complete merely because CI is green. All conditions below must hold:

1. 56/56 Design Assignment requirements are structurally represented.
2. Every requirement has a verification kind and route or an explicit route limitation.
3. No `COMPLIANT`/`NONCOMPLIANT` without addressable canonical evidence.
4. No categorical result without proven object/parameter/decision binding where ownership is required.
5. Table-of-contents evidence cannot satisfy proof.
6. No cross-owner comparison.
7. Every categorical result traces to document, page, fragment, binding, proof, and decision.
8. Historical Test 78 defects are represented in Golden Set regression tests.
9. Existing `core20` regression suite remains green.
10. AI/Judge/Critic failure, timeout, 429, or unavailable provider cannot be converted into a completed successful verification.

## Quality KPI
Primary KPI is **maximum correctly automated requirements at near-zero false-positive proof**, not raw automation percentage.

A truthful `REVIEW` is better than an unsupported `COMPLIANT`.

## Compatibility strategy
- Stable branch remains `codex/expertcheck-20.0`.
- 25.0 work occurs on `codex/expertcheck-25.0-quality-leap`.
- `core20` remains usable as reference/baseline and through adapters.
- New categorical behavior is implemented only in `core25`.

## Initial package responsibilities

- `core25/contracts.py` — strict immutable-ish verification contracts and enums.
- `core25/integrity.py` — proof/decision precondition gates.
- `core25/requirement_engine.py` — atomic requirement normalization/classification.
- `core25/routing.py` — expected evidence routes and proof-slot contracts.
- `core25/evidence.py` — evidence candidate normalization and eligibility.
- `core25/binding.py` — semantic owner and parameter/decision binding.
- `core25/proof.py` — canonical proof construction.
- `core25/decision.py` — final state machine.
- `core25/pipeline.py` — orchestration and trace.
- `core25/adapters/core20.py` — compatibility with proven `core20` outputs.
- `tests/core25/golden/` — Test 78 and other permanent regressions.

## Non-goals for Alpha 1
- Full rewrite of UI.
- Full automation of all 544 checklist items.
- Removing `core20`.
- Maximizing automatic `Yes/No` coverage at the expense of proof integrity.
- Broad domain-specific rule expansion before the common verification core is proven.
