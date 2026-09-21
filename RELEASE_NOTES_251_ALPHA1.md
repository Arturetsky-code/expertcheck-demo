# ExpertCheck 25.1 Alpha 1 — Runtime Integrity

Branch: `codex/expertcheck-25.1-runtime-integrity`

## Purpose

25.1 is deliberately not a coverage release. It fixes contradictions exposed by the
first real user Test 78 on 25.0 before the project moves into the coverage-first
25.2 phase.

## Test 78 baseline that triggered this release

- Assignment: 56 requirements; Core25 UI showed 2 categorical matches, while XLSX
  demoted them back to review.
- AI telemetry: cumulative counters reported more completed Judge/Critic work than
  the row-level execution trace could prove.
- Completeness: the report wrote «Подтверждена» although the matrix itself showed
  an incomplete package; confirmation and completeness were conflated.
- Risk Intelligence: review-only comparison diagnostics could be promoted to
  «Высокий» by historical scenario severity.
- Positive result retained: object/parameter binding no longer confuses the
  89.9 m² building area with the 23.5 m² dust-suppression module area.

## 25.1 changes

1. **Single categorical Assignment verdict path**
   - Core25 public rows carry an explicit integrity-passed marker.
   - The legacy Verified Core gate no longer re-adjudicates a valid Core25 proof
     with incompatible 17.0 proof vocabulary.
   - A Core25 categorical result is still fail-closed unless decision, proof state,
     proof id, trace id and addressable evidence are mutually consistent.

2. **Fail-closed AI telemetry**
   - Current L4 packet rows are authoritative for the queue size.
   - A completed response counts only when it is attached to the current packet row
     and can be reproduced from the checkpoint.
   - Stale/orphan checkpoint ids are pruned and reopened instead of inflating
     completion counters.
   - XLSX exposes telemetry integrity/repair counters.

3. **Risk severity integrity**
   - Knowledge-base recurrence may prioritize a real finding, but cannot elevate a
     REVIEW question above the maximum level allowed by finding qualification.

4. **Completeness semantics**
   - «Неполный комплект» / «Комплект формируется» / «Требует уточнения» is now kept
     separate from «матрица подтверждена пользователем».
   - Reports show actual completeness status, coverage and missing mandatory
     sections separately from user confirmation.

## Release gate

Status: **NOT_READY_FOR_MANUAL_TEST** until Core25/Core20 CI and the new 25.1
runtime-integrity regressions are green.

After CI, the intended manual check is a short Test 78 integrity rerun. A full
coverage run is deferred to 25.2 Coverage Breakthrough.
