# ExpertCheck 25.2 — validated checkpoint 22/56

Date: 2026-09-24  
Branch: `codex/expertcheck-25.2-coverage-breakthrough`

## Accepted benchmark

Test 78 / Assignment compliance / AI off:

- requirements: 56
- compliant: 20
- proven deviations: 2
- review-only: 34
- strict categorical coverage: **22/56 = 39.3%**

## New accepted result

Requirement: `ASSIGN-618EAB7B243E86`  
Text: `Навес системы подачи извести (поз. 4.25) выполнить открытым`

State change:
`REVIEW_QUESTION -> VERIFIED_OK`

Core25:
- proof state: `PROVEN_MATCH`
- reason: `ASSIGNMENT_PRESENCE_CONFIRMED`
- executor: `OPEN_CANOPY_DRAWING_EXECUTOR`

Evidence:
- AR2 page 33: exact owner/position; facade directions, section and profiled roof decking;
- KR2 page 172: independent open-frame corroboration by columns / vertical bracing and roof beams / purlins.

## A/B

Control:
- 19 `VERIFIED_OK`
- 37 `REVIEW_QUESTION`

Validated:
- 20 `VERIFIED_OK`
- 36 `REVIEW_QUESTION`

Exactly one of the 56 requirements changed state: `ASSIGN-618EAB7B243E86`.

The two previously accepted deviations are unchanged; therefore official coverage is
**20 compliant + 2 deviations = 22/56**.

## False-positive safeguards

- canopy wording alone is insufficient;
- exact position and title-block owner are mandatory;
- the owner must also be named by the Assignment requirement;
- drawing indexes are not proof;
- drawing-sheet titles cannot become owners;
- wall / sandwich-panel evidence blocks open-canopy proof;
- AR requires multiple facades + section + roof solution;
- KR frame corroboration is mandatory;
- only atomic `PRESENCE_REQUIREMENT` can use this executor.

## Validation chain

Drawing-proof source used by Test78 A/B:
`8b2d798939cc953ef77101652556ecbebd1ccf2d`

Validated source/control commit:
`a1855a657fcf069a6ab377578248edde2da61647`

Green validation marker:
`aab7ac19d96e163e5cad6e4bfda33aea2723510b`

Validation results:
- direct coverage-breakthrough regression: passed;
- direct Core25 regression package: passed;
- Core25 tests: passed;
- Core20 regression: passed;
- mandatory focused regressions: passed;
- legacy full repository suite against baseline allowlist: passed;
- Core25 compile: passed.

## Continue from here

Official next baseline is **22/56**. Electrical lighting remains 4/5; power supply remains
6/8; the composite lime-supply requirement remains review-only because 1 m3 MКР volume is
not proven by the available 1000 kg project evidence.
