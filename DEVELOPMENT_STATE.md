# ExpertCheck development state

Updated: 2026-09-23
Active branch: `codex/expertcheck-25.2-coverage-breakthrough`
Latest validated checkpoint commit: `e37a7e805fd4e3c3a674944e81e2fa5462aa71e0`

## Official accepted local checkpoint

Assignment compliance / Test 78 / AI off:

- Requirements: 56
- `Соответствует заданию`: 18
- Proven deviations: 2
- `Требует проверки`: 36
- Strict categorical coverage: **20/56 = 35.7%**
- Admission diagnostics include **PROFILE_SECTION_ABSENT**
- Test 78 count at PROFILE_SECTION_ABSENT: **15 requirements**

Accepted categorical deviations:
- Requirement 22: loader identity/quantity mismatch.
- Requirement 3: Appendix 1 identification responsibility mismatch for exact GP position **4.25 “Навес системы подачи извести”**: Assignment **КС-2, γn=1.0** vs KR **КС-3, γn=1.1**.

New accepted compliance since 18/56:
- Requirement 12 via `NORMATIVE_DESIGN_ADOPTION_EXECUTOR`: the Assignment-mandated СП 45.13330.2017 is addressably adopted in the project design chain. This is only an Assignment→PD verdict and does not substitute for full normative compliance checking.

Validation:
- `tests/core25/test_coverage_breakthrough_252.py`: **27/27 passed**
- Other available Core25 tests: **106 passed**
- One historical test remains blocked only because `validation_reports_150a2/ExpertCheck_Отчёт_ГИПа_15.0A2.xlsx` is absent from the source snapshot.

## Missing-profile-section policy

This is an established fail-closed rule, not a new feature:

1. absence of the expected profile section cannot prove compliance;
2. absence of the expected profile section cannot prove a deviation;
3. runtime diagnostics must distinguish `PROFILE_SECTION_ABSENT` from retrieval/proof failure where the profile section is present.

Examples in Test 78:
- ИОС3 absent -> sewerage requirement stays review-only;
- ИОС4 absent -> heating/ventilation requirements stay review-only;
- ИОС5 absent -> cellular/radio/video requirements stay review-only;
- ИОС6 absent -> gasification requirement stays review-only;
- OOS/PB/EE/ODI/POS requirements are likewise marked by missing expected sections where those sections are not in the 12-file package.

## Validated improvement after 18/56

Requirement 12 is now categorically confirmed by `NORMATIVE_DESIGN_ADOPTION_EXECUTOR`:
- PZU provides an addressable engineering-preparation solution;
- KR/PZU provide addressable adoption of the same `СП 45.13330.2017` for the corresponding earthwork/foundation work;
- Core25 proof reason: `ASSIGNMENT_NORMATIVE_DESIGN_ADOPTION_CONFIRMED`;
- proof metadata explicitly records that full normative compliance itself was **not** assessed. That remains a separate NTD-contour task.

This executor must not close a requirement from a normative citation alone: both an addressable design solution and adoption of every required cited norm are required.

## Safety hardening at the 19/56 checkpoint

The 19/56 count is unchanged, but the checkpoint is stronger:

- fixed false metric extraction: the adjective `объёмно-планировочный` no longer creates a false `VOLUME` parameter;
- requirement 13 now routes correctly to `ПЗУ`;
- `ПУЭ` is recognized as a mandatory normative reference by Assignment normative-adoption checks;
- a normative bibliography/list is not accepted as proof that a standard was adopted by the design;
- normative adoption must be local to the cited norm and contain an explicit adoption/application cue;
- requirement 13 therefore remains `Требует проверки`: SP 4 and SP 37 have addressable application evidence, while SP 18 is only listed in the bibliography and PUE is not found in the PZU evidence set;
- requirement 12 remains safely categorical because its design solution and SP 45.13330.2017 adoption are both addressably proven.

## Current development priority

Do not revisit missing-section fail-closed logic unless a regression appears.

Continue with requirements where the expected section IS present but proof is not closed:
- 33 Water supply (ИОС2 present): most conditions are present, but factory-supply wording for the module tanks is not yet addressably proven.
- 39 Automation (ТХ/PЗ present): many ASU functions are proven, but complete-supply and reserve-aggregate/productivity conditions are not fully proven.
- 40 Power supply (ИОС1 present): many clauses are proven (overhead lines, SIP, cable trays, no buried routing, DGS/category-I reserve, PUE/FNP); support-on-concrete-footings remains to be proven before categorical closure.

After these, prioritize other `PROFILE_SECTION_PRESENT` rows by admission stage rather than chasing raw coverage.

## WIP preserved but not accepted

Identification-register executor experiment:
- produced an extra categorical mismatch for requirement 3;
- not yet manually audited;
- was rolled back from the accepted local runtime;
- WIP tests/research must be preserved separately and revisited later, not silently merged into the accepted checkpoint.

Operating-regime evidence ranking improvement is also WIP: prefer project-wide DSK regime evidence over a coincidental 12-hour shift of a local subsystem.

## Checkpoint protocol — mandatory

Use GitHub as the durable development journal.

Create a checkpoint:
- at most every **20 minutes of active development** when changes exist;
- immediately after any audited benchmark improvement;
- immediately after a green regression package;
- before a substantial architectural experiment;
- before ending work, switching chats, or when the chat is becoming large.

Checkpoint types:
- **WIP checkpoint** — preserves unfinished experiments without promoting them to the accepted baseline.
- **Validated checkpoint** — benchmark reproduced, false-positive audit completed for new categorical results, tests recorded.

Every validated checkpoint records:
- exact branch / commit SHA or recovery delta;
- Test 78 counts;
- tests passed / blocked and why;
- new categorical requirements and their evidence audit;
- false-positive safeguards;
- unfinished next step.

Do not rely on chat history or ephemeral local filesystem as the only record of development progress.
