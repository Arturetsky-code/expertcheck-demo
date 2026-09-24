# ExpertCheck 25.2 — validated checkpoint 25/56

Date: 2026-09-24  
Branch: `codex/expertcheck-25.2-coverage-breakthrough`

## Accepted benchmark

Test 78 / Assignment compliance / AI off:

- requirements: 56
- compliant: 23
- proven deviations: 2
- review-only: 31
- strict categorical coverage: **25/56 = 44.6%**

## New accepted result

Requirement: `ASSIGN-6D099E6177F344`  
Text: `Инженерную подготовку территории предусмотреть в соответствии с СП 45.13330.2017 ...`

State change:
`REVIEW_QUESTION -> VERIFIED_OK`

Executor:
`NORMATIVE_DESIGN_ADOPTION_EXECUTOR`

Core25:
- proof state: `PROVEN_MATCH`
- reason: `ASSIGNMENT_NORMATIVE_DESIGN_ADOPTION_CONFIRMED`

Proof slots:
1. addressable engineering-preparation design solution;
2. addressable adoption of every norm explicitly named by the Assignment.

This proof confirms transfer of the Assignment requirement into PD only.
Full normative compliance is not assessed by this route.

## A/B

24/56 baseline:
- 22 `VERIFIED_OK`
- 34 `REVIEW_QUESTION`

Validated:
- 23 `VERIFIED_OK`
- 33 `REVIEW_QUESTION`

Exactly one requirement changed state: `ASSIGN-6D099E6177F344`.

With the two unchanged proven deviations, official strict coverage is:
**23 compliant + 2 deviations = 25/56**.

## Validation chain

Validated source:
`fded177104b8527978ea7431873e9b99b3a7a768`

Green direct-validation marker:
`9e82f3fbd66bc005164a380eeece825507624928`

Passed:
- coverage-breakthrough regression;
- Core25 regression package;
- Core25 Quality Leap;
- Core20 regression;
- baseline full diagnostic;
- mandatory focused regressions;
- legacy full repository suite against baseline allowlist;
- Core25 compile.

## Rejected duplicate experiment

The temporary stockpile-to-technological-complex access executor was removed.
The target requirement was already categorical under the existing
`PERSONNEL_AND_VEHICLE_ACCESS` executor and A/B showed zero coverage gain.

## Continue from here

Official next baseline is **25/56**.

Next audited candidate:
`ASSIGN-38E7D1D078444D` — foundations for crushing equipment under dynamic loads.
The current project contains addressable foundation design, SP 26.13330.2012 adoption,
calculated vibration amplitude 0.1 mm vs allowable 0.3 mm, and foundation drawings.
Because the Assignment does not name a specific standard, use a stricter generic-normative
proof rather than the named-norm adoption route.
