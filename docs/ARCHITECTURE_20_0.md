# ExpertCheck 20.0 — Canonical Engineering Architecture

## Why 20.0 exists

18.x proved several high-value mechanisms but accumulated multiple representations of the same engineering fact across Project Understanding, cross-section checks, report gates, result surfaces, runtime patches and persistence recovery.

20.0 replaces that architecture gradually, under parity control, instead of rewriting the product in one unsafe cut-over.

## Product workflow

Target user flow:

`Комплект → Модель проекта → Проверка → Требует решения → Результаты → Отчёт`

Judge/Critic, evidence levels, checkpoints, provider routing and internal diagnostic gates belong to developer mode rather than the primary GIP workflow.

## Canonical Engineering Core

Every engineering statement must resolve into one of the canonical entities:

- `ProjectObject` — trusted project object / component;
- `PropertyValue` — object → parameter → value → unit;
- `Requirement` — what must be checked and where evidence is expected;
- `Evidence` — addressable document/page/table/row fragment;
- `Comparison` — deterministic relation between canonical properties/evidence;
- `Finding` — VERIFIED_OK / PROJECT_FINDING / REVIEW_QUESTION / SYSTEM_LIMITATION;
- `CanonicalProject` — reference-integrity boundary and single source of truth.

Core rule: **one engineering fact = one canonical record**. UI pages and reports are projections of canonical state, not independent result stores.

## Migration strategy

### Phase A — Dual Run

18.7.3 stays authoritative. `Legacy18Adapter` builds a compact 20.0 canonical model in parallel. 20.0 is observational and cannot change verdicts.

### Phase B — Verification Engine 2.0

Requirements execute through one contract:

`applicability → binding → evidence route → deterministic checker → AI only if necessary → independent validation → verdict`

### Phase C — Domain migration

Order:

1. cross-section verification;
2. assignment compliance;
3. high-value checklist contracts;
4. normative requirements;
5. Drawing Intelligence.

### Phase D — Canonical persistence

PostgreSQL stores canonical project state and user decisions directly. Snapshot recovery becomes versioned canonical migration rather than runtime reconstruction.

### Phase E — Engineering UX

Primary workflow is rebuilt around engineer actions. Technical engines remain visible only in developer mode.

## Baseline 18.7.3 — Test 77

| Metric | Baseline | 20.0 policy |
| --- | ---: | --- |
| Confirmed objects | 36 | EXACT during migration |
| Passport characteristics | 137 | AT LEAST |
| Cross-section comparisons | 99 | EXACT during migration |
| Cross-section L5 | 45 | AT LEAST |
| Project findings | 1 | EXACT on golden project |
| Specialist questions | 346 | AT MOST |
| Review packages | 26 | AT MOST |
| Verified checks | 49 | AT LEAST |
| System limitations | 319 | AT MOST |

## Golden cases

### GOLD-COMPRESSOR-AREA-CONFLICT

Compressor / AREA_BUILD: PZ 54.3 m² vs PZU 48.7 m².

Required outcome: PROJECT_FINDING. Conflict fact is confirmed; correct/current value remains unverified without the owner-section route.

### GOLD-DEDUSTING-AREA

Dedusting module, GP position 4.12: AREA_BUILD = 23.5 m².

23.5 m² must never migrate to the sample preparation building.

### GOLD-SAMPLE-PREP-AREA

Sample preparation building, GP position 4.13: AREA_BUILD = 89.9 m².

89.9 m² must remain bound to the physical/semantic row of that object.

## Release gates

A 20.0 component may replace its 18.x counterpart only when:

1. canonical reference validation has zero ERROR issues;
2. all golden cases pass;
3. accepted 18.7.3 findings are preserved;
4. no false-positive regression is observed on the golden project;
5. required baseline metrics satisfy their policy;
6. UI and report consume the same canonical projection.

## Non-goals of Alpha 1

- no new AI model/provider;
- no deletion of legacy core;
- no new PDF extraction;
- no change to accepted verdicts;
- no full UX redesign yet.
