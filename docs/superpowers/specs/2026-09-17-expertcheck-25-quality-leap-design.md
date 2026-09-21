# ExpertCheck 25.0 Quality Leap — Design

## Status
Approved architecture for the 25.0 generation. Base branch remains `codex/expertcheck-20.0`; implementation branch is `codex/expertcheck-25.0-quality-leap`, created from stable commit `6afaf020f329f07bdbce6d0ea2c0e1238023aed6`.

## Purpose
ExpertCheck 25.0 is not a feature-number bump. It is a consolidation of the verified mechanisms created in 9.x–20.0 into one strict verification architecture that can serve Assignment Compliance, normative checks, checklists, and cross-section engineering comparison.

The product goal is to move from document search plus domain-specific proof paths to a single auditable verification pipeline:

`Requirement → Route → Evidence → Binding → Proof → Decision → Trace`

The first vertical proof of the new architecture is Design Assignment compliance.

## Core architectural decision
Use a new `core25` package next to `core20`.

`core20` remains the stable control implementation. `core25` imports proven `core20` mechanisms only through explicit adapters. We do not perform a big-bang rewrite and we do not mix new 25.0 rules directly into `core20`.

This provides three guarantees:

1. regression safety against the stable 20.0 baseline;
2. explicit migration boundaries;
3. the ability to prove new behavior before replacing old paths.

## Guiding invariant
No correct binding means no proof. No proof means no categorical verdict.

A `COMPLIANT` or `NONCOMPLIANT` decision is forbidden unless the system can trace the decision to addressable canonical evidence that is bound to the correct engineering owner and semantic parameter.

AI confidence, semantic similarity, and Judge/Critic output can support candidate discovery and review, but cannot alone satisfy the proof gate.

## Domain model
The canonical 25.0 model extends the concepts already present in `core20/model.py` and makes the verification chain explicit.

### Requirement
Represents one atomic checkable condition.

Required concepts:
- stable requirement id;
- domain (`ASSIGNMENT`, `NORMATIVE`, `CHECKLIST`, `CROSS_SECTION`);
- source text and source address;
- requirement type;
- target object or project-global scope;
- expected parameter or decision concept;
- required value/unit/topology/presence condition where applicable;
- expected evidence routes;
- verification contract;
- trace metadata.

### Evidence
Represents one addressable source fragment.

Required concepts:
- stable evidence id;
- document id/name;
- document type/section;
- page;
- table/row/cell address when available;
- exact fragment;
- extraction/source kind;
- addressability;
- provenance/trust information;
- structured facts detected in the fragment.

An index entry, table of contents entry, generic document title, or unaddressable semantic hit cannot by itself be promoted to canonical proof evidence.

### Binding
A binding is a separate first-class result, not a side effect of retrieval.

It answers:
- Which project object owns this evidence/value?
- Which engineering parameter or project decision does it represent?
- Is the owner project-global or object-specific?
- What evidence supports the ownership decision?
- Is the binding deterministic, structured, semantic, inferred, or unresolved?

Required states:
- `BOUND`;
- `AMBIGUOUS`;
- `UNBOUND`;
- `REJECTED`.

A value with `AMBIGUOUS`, `UNBOUND`, or `REJECTED` owner state is prohibited from producing a categorical mismatch.

### Proof
Proof combines a Requirement with one or more correctly bound Evidence records.

Required proof states:
- `PROVEN_MATCH`;
- `PROVEN_MISMATCH`;
- `CONFLICT`;
- `INSUFFICIENT`;
- `NOT_APPLICABLE`;
- `SYSTEM_LIMITATION`.

Proof always records the exact evidence and binding ids that caused the state.

### Decision
Decision maps proof into user-facing outcome without inventing certainty.

Initial Assignment decision states:
- `COMPLIANT`;
- `NONCOMPLIANT`;
- `REVIEW`;
- `NOT_APPLICABLE`;
- `LIMITATION`.

Only `PROVEN_MATCH` may yield `COMPLIANT`. Only `PROVEN_MISMATCH` may yield `NONCOMPLIANT`.

## Package structure
Create `core25/` with focused modules.

- `contracts.py` — dataclasses/enums for Requirement, Evidence, Binding, Proof, Decision and Trace.
- `requirement_engine.py` — atomic requirement normalization/classification for Design Assignment first.
- `routing.py` — verification contract and expected evidence route selection.
- `evidence.py` — evidence candidate collection and canonical evidence qualification.
- `binding.py` — object/parameter/decision ownership proof.
- `proof.py` — deterministic proof assembly and integrity gates.
- `decision.py` — proof-to-decision mapping.
- `pipeline.py` — orchestrates the full vertical flow.
- `adapters/core20.py` — explicit adapters to stable `core20` parsers, parameter contracts, normative helpers and page corpus structures.
- `golden/` — Golden Set fixtures and regression expectations derived from Test 78 defects.

Files remain small enough that each responsibility can be understood and tested independently.

## Assignment Compliance vertical slice
25.0 Alpha 1 runs all 56 known Design Assignment atomic requirements through the same core pipeline.

For each requirement:

1. reconstruct or import the atomic requirement;
2. assign project-global or object-specific scope;
3. determine the verification kind and evidence route;
4. collect candidate evidence;
5. reject non-canonical evidence such as contents/index-only hits;
6. bind each candidate to owner + parameter/decision concept;
7. assemble proof;
8. emit a decision;
9. persist a full trace.

The engine may return `REVIEW` or `LIMITATION`. Coverage is not allowed to increase by manufacturing proof.

## Supported Alpha 1 verification kinds
The first release must support the cases already demonstrated in 20.0 and route them through one contract system:

- typed numeric value;
- presence of an object/project decision;
- equipment working/reserve topology;
- project-global numeric requirement;
- structured table-cell requirement;
- unsupported semantic requirement routed to `REVIEW` rather than false confirmation.

The architecture must allow future proof plugins without changing the pipeline contract.

## Binding rules
Object-specific requirements must match the engineering owner before comparison.

A correct parameter code with the wrong owner is not proof.

A correct owner with a semantically different parameter is not proof.

Project-global requirements may explicitly opt out of object ownership only when their verification contract declares `PROJECT_GLOBAL`.

The known class of error `Здание проборазделки 89,9 м²` versus `Модуль обеспыливания 23,5 м²` must be impossible to promote to a confirmed mismatch because the owner binding differs.

## Evidence integrity rules
Canonical evidence must be addressable and auditable.

The following are insufficient alone:
- table of contents;
- section title;
- document filename;
- search-result snippet with no page address;
- semantic similarity score;
- LLM statement without source fragment;
- Judge/Critic agreement without canonical evidence.

Every categorical result must retain document, page and fragment; table/row/cell coordinates are retained where available.

## AI role
AI is a candidate generator and semantic assistant, not the source of final truth.

Allowed AI roles:
- requirement decomposition suggestions;
- candidate evidence ranking;
- synonym/concept expansion;
- ambiguity detection;
- Judge/Critic challenge of an already constructed proof.

AI cannot independently upgrade `INSUFFICIENT` evidence to `PROVEN_MATCH` or `PROVEN_MISMATCH`.

Provider failure, rate limit, timeout, or unavailable model must degrade the affected check to a retryable/review/limitation state and must never be recorded as a successful verification.

## Golden Set
Test 78 becomes a regression source rather than a mandatory manual run after each micro-change.

The initial Golden Set must include at least these defect classes:
- table-of-contents evidence rejected;
- wrong object owner rejected;
- wrong semantic parameter rejected;
- owner section absent;
- persistence/reload preserves proof trace;
- Judge/Critic cannot override missing canonical proof;
- provider 429/failure is not successful result;
- `nan`/invalid values cannot leak into categorical proof or reports;
- canonical proof survives report export;
- positive semantic verdict without selected addressable evidence is rejected.

New user-discovered defects are added to the Golden Set before the corresponding fix.

## Compatibility and migration
`core20` remains untouched except where an adapter-compatible read-only extension is unavoidable and separately regression-tested.

Alpha 1 may dual-run selected Assignment cases between 20.0 and 25.0 for diagnostics, but 25.0 decisions must be generated from the new core25 pipeline.

Existing 20.0 regression tests remain mandatory.

## Reporting contract
Every categorical report statement must expose or persist a trace to:

`Decision → Proof → Binding → Evidence → document/page/fragment`.

Reports must distinguish:
- verified compliance;
- verified noncompliance;
- requires review;
- system limitation;
- not applicable.

Raw `nan`, stale version labels, provider errors, or internal proof-state names must not leak into user-facing reports.

## Alpha 1 acceptance gates
Alpha 1 is not complete merely because CI is green. All gates below are required.

1. All 56 known Assignment requirements are represented as atomic Requirement records.
2. 56/56 have an explicit scope and verification route, including unsupported routes that intentionally end in review.
3. Zero `COMPLIANT` or `NONCOMPLIANT` decisions are emitted without addressable canonical evidence.
4. Zero categorical cross-owner comparisons are allowed.
5. Table-of-contents/index-only evidence cannot satisfy proof.
6. Every categorical decision is traceable to document + page + fragment.
7. Initial Test 78 Golden Set is automated and green.
8. Existing core20 regression suite remains green.
9. AI/provider failure cannot become a completed positive verification.
10. Persisted/reloaded decisions preserve their canonical trace.

## Quality KPI
The principal KPI is precision of automatic proof, not the number of automatic verdicts.

Target behavior: maximize the number of correctly automated requirements while keeping false-positive categorical proof effectively at zero on the Golden Set and control package.

A release that proves 30 requirements correctly and routes 26 to review is preferable to one that claims 50/56 with weak or wrong evidence.

## Out of scope for Alpha 1
The following remain 25.0 goals but are not allowed to dilute the first vertical slice:
- migration of all normative checks to core25;
- full checklist coverage;
- full cross-section migration;
- new UI redesign;
- large-package performance optimization;
- broad new industry rule catalogues.

After the Assignment vertical slice passes the acceptance gates, the same contracts are extended to normative checks, cross-section comparison, then the first high-confidence checklist pack.
