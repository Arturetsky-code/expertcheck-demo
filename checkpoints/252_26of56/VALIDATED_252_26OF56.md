# ExpertCheck 25.2 — validated checkpoint 26/56

Date: 2026-09-24  
Branch: `codex/expertcheck-25.2-coverage-breakthrough`

## Accepted benchmark

Test 78 / Assignment compliance / AI off:

- requirements: 56
- compliant: 24
- proven deviations: 2
- review-only: 30
- strict categorical coverage: **26/56 = 46.4%**

## New accepted result

Requirement: `ASSIGN-38E7D1D078444D`  
Text: `Основания для установки технологического оборудования дробильного комплекса выполнить согласно нормативным требованиям к основаниям технологического оборудования с динамическими нагрузками`

State change:
`REVIEW_QUESTION -> VERIFIED_OK`

Executor:
`DYNAMIC_FOUNDATION_NORMATIVE_EXECUTOR`

Core25:
- proof state: `PROVEN_MATCH`
- reason: `ASSIGNMENT_DYNAMIC_FOUNDATION_NORMATIVE_CONFIRMED`

## Required evidence

All four are mandatory:

1. project foundation solution for crushing equipment;
2. addressable adoption of SP 26.13330.2012 for machine foundations under dynamic loads;
3. quantitative vibration calculation with calculated value <= allowable limit;
4. independent KR graphical corroboration of the corresponding foundation plates.

Real Test78 evidence:
- KR1 p74: foundation solution and SP26 adoption;
- KR1 p74: 0.1 mm calculated vibration amplitude <= 0.3 mm allowable;
- KR2 p31: foundation-plate scheme ФПм1 / ФПм2 / ФПм3 for crushing-complex equipment.

## A/B

25/56 baseline:
- 23 `VERIFIED_OK`
- 33 `REVIEW_QUESTION`

Validated dynamic-foundation source:
- 24 `VERIFIED_OK`
- 32 `REVIEW_QUESTION`

Exactly one requirement changed state: `ASSIGN-38E7D1D078444D`.

With two unchanged proven deviations:
**24 compliant + 2 deviations = 26/56**.

## False-positive safeguards

- bibliography-only SP26 is insufficient;
- missing dynamic calculation is insufficient;
- missing drawing is insufficient;
- drawing without calculation is insufficient;
- calculated amplitude above allowable limit is rejected;
- full normative compliance with all SP26 clauses is not claimed by this Assignment proof.

## Validation chain

Validated source:
`647291933d2b48fe84318891a2845c5e4cb01008`

Green marker:
`ecfb2e432e2b0c43e545d268643793c07562468b`

Passed:
- direct coverage-breakthrough regression;
- full Core25 regression package;
- Core25 Quality Leap;
- Core20 regression;
- baseline full diagnostic;
- mandatory focused regressions;
- legacy full suite against baseline allowlist;
- Core25 compile.

## Continue from here

Official next baseline is **26/56**.
Continue only with a genuinely review-only requirement that has an addressable project-side evidence path.
