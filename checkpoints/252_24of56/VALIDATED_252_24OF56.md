# ExpertCheck 25.2 — validated checkpoint 24/56

Date: 2026-09-24
Branch: `codex/expertcheck-25.2-coverage-breakthrough`

## Accepted benchmark

Test 78 / Assignment compliance / AI off:

- requirements: 56
- compliant: 22
- proven deviations: 2
- review-only: 32
- strict categorical coverage: **24/56 = 42.9%**

## New accepted result

Requirement: `ASSIGN-B52474791A34FB`
Source row: 48
Instruction: `Определить при разработке документации`
Subject: landscaping / small architectural forms / site planning.

State change:
`REVIEW_QUESTION -> VERIFIED_OK`

Executor:
`LANDSCAPING_DESIGN_DETERMINED_EXECUTOR`

Required 3/3 proof:
1. textual PZU landscaping solution;
2. graphical landscaping plan;
3. concrete surfacing / pedestrian / small-form elements.

A/B on the same 56 requirements changed exactly one row:
- before: 21 VERIFIED_OK / 35 REVIEW_QUESTION
- after: 22 VERIFIED_OK / 34 REVIEW_QUESTION

With the two unchanged proven deviations:
**22 compliant + 2 deviations = 24/56**.

Validated source:
`0013ba07a409cef81f117ececcb5489130f50722`

Green marker:
`f817001a295a29dcb07d847565870a94fad3ff9c`

All Core20/Core25/direct validation gates: **success**.
