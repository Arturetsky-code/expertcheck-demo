# ExpertCheck development state

Updated: 2026-09-23
Active branch: `codex/expertcheck-25.2-coverage-breakthrough`
Latest validated checkpoint commit: `b8cad2b66364f13802b682318da1b7ce7d5732d3`

## Official accepted local checkpoint

Assignment compliance / Test 78 / AI off:

- Requirements: 56
- `Соответствует заданию`: 19
- Proven deviations: 2
- `Требует проверки`: 35
- Strict categorical coverage: **21/56 = 37.5%**
- Admission diagnostics include **PROFILE_SECTION_ABSENT**
- Test 78 count at PROFILE_SECTION_ABSENT: **15 requirements**

Accepted categorical deviations:
- Requirement 22: loader identity/quantity mismatch.
- Requirement 3: Appendix 1 identification responsibility mismatch for exact GP position **4.25 “Навес системы подачи извести”**: Assignment **КС-2, γn=1.0** vs KR **КС-3, γn=1.1**.

New accepted compliance at 21/56:
- Requirement 10 / “Срок строительства объекта”: Assignment says “Определить проектной документацией”; PZ page 27 contains the structured project fact **“Сведения о сроках проведении работ: Продолжительность работ, месяц: 12”**.
- Core25 now has a separate `DESIGN_DETERMINED` route/proof so structured project values are not forced through ordinary PRESENCE wording.
- Secondary clauses such as “Размеры определить проектом” no longer reclassify a composite engineering requirement (e.g. fencing/gates/wickets) away from PRESENCE.

Safety retained:
- TOC/header text alone still cannot prove construction duration.
- The duration proof requires addressable profile evidence and a positive structured value/project assertion.
- Existing fencing result remains categorical; no coverage was gained by weakening its gate.

Validation:
- `tests/core25/test_coverage_breakthrough_252.py`: **29/29 passed**
- Other available Core25 tests: **79/79 passed**
- One historical Assignment pipeline test is deselected/blocked only because `validation_reports_150a2/ExpertCheck_Отчёт_ГИПа_15.0A2.xlsx` is absent from the source snapshot.

Recovery:
- Start from the validated 20/56 checkpoint and apply `checkpoints/252_21of56/CHECKPOINT_252_21OF56_INCREMENT.patch`.


## Validated quality checkpoint — composite condition diagnostics

The strict Test 78 verdict remains **21/56 = 37.5%** (19 compliant + 2 proven deviations). No partial condition evidence is allowed to promote a whole composite requirement.

Condition-level diagnostics now expose:
- Water supply (source row 30): **4/5** conditions proven. Missing: factory-complete supply of the modular-building tanks.
- Automation (source row 37): **7/10** conditions proven. Missing: ASU complete supply; productivity control via additional/reserve aggregates; explicit optimal-mode condition.
- Power supply (source row 38): **5/8** conditions proven. Missing: supports on concrete footings; DGS for the broader category-I requirement; addressable adoption of both mining-safety FNP and PUE (a bibliography hit is not enough).

Safety rules:
- partial slot evidence is emitted only as `candidate`, never `verified_candidate`;
- category-I special-group DGS evidence cannot prove the broader category-I Assignment condition;
- generic normative bibliography references cannot prove design adoption;
- condition diagnostics are explanatory only until every material slot is proven.

Report/UI surface:
- Assignment diagnostic rows now include `Условия доказаны` and `Неподтверждённые условия`;
- GIP and technical XLSX reports include a dedicated `Задание — условия` sheet with per-condition document/page/evidence traces.

Validation:
- `tests/core25/test_coverage_breakthrough_252.py`: **33/33 passed**;
- other available Core25 tests: **79/79 passed** (same historical missing-XLSX fixture deselected);
- report/result integrity selection: **10/10 passed**;
- Test 78 deterministic benchmark reproduced at **21/56**.

Recovery delta:
- `checkpoints/252_21of56/RECOVERY_252_21OF56_CONDITION_MATRIX.patch.gz.b64`

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


## Session-end checkpoint — 2026-09-23

Accepted baseline remains **Test 78 = 21/56 (37.5%)**:
- 19 compliant;
- 2 proven deviations;
- 35 review-only.

Manual evidence audit completed before ending the session:
- Water supply remains **4/5 conditions proven**. The missing factory-complete-supply condition for tanks serving modular buildings is not addressably proven. The phrase about factory-complete supply in IOS2 refers to fire-water reservoirs and must not be borrowed across subjects.
- Automation remains **7/10 conditions proven**. No addressable proof was found for ASU complete supply, productivity control by starting additional/reserve aggregates, or an explicit optimal-operating-mode condition.
- Power supply remains **5/8 conditions proven**. No addressable proof was found for supports on concrete footings; DGS is tied to the special group of category I rather than category I generally; PUE has a local application example, while FNP No. 505 is only listed in the normative bibliography and therefore cannot close the full adoption condition.
- No checker was weakened and no categorical result was added from these three audits.

Repository integrity note:
- all validated 21/56 work is preserved in GitHub;
- the recovery chain 18→21/56 has now been materialized into the normal source tree by `.github/workflows/recover-252.yml`;
- the workflow validates `tests/core25/test_coverage_breakthrough_252.py` and the Core25 regression package before committing recovered source;
- the current branch contains the materialized Core/Core25/test changes, so the branch is self-contained for further development;
- checkpoint/recovery files remain as disaster-recovery history only and are no longer required as the normal runtime source.

No new runtime/code changes were accepted on 2026-09-23 after the 21/56 checkpoint.


## WIP checkpoint — 2026-09-24 strict composite proof routing

Official accepted benchmark remains **Test 78 = 21/56 (37.5%)** until a fresh full regression/benchmark reproduction is completed.

### Lightning and grounding — strong candidate for 22/56

Requirement row 40 has been manually audited against IOS1 and all five mandatory conditions are addressably proven:
1. protective grounding device;
2. lightning receptors on lighting masts;
3. metallic building structures for buildings outside mast protection zones;
4. addressable adoption of RD 34.21.122-87;
5. addressable adoption of SO 153-34.21.122-2003.

The specialized `LIGHTNING_GROUNDING_COMPOSITE_EXECUTOR` now:
- runs before the generic normative checker;
- requires 5/5 conditions before any evidence becomes `verified_candidate`;
- emits qualified normative evidence only after the full composite gate is closed;
- supports both the legacy presence route and a normative route without weakening either generic proof rule.

Regression coverage was extended with split-page IOS1 evidence and Core25 admission tests.

### Electrical lighting — deliberately held at 4/5

Requirement row 39 is now handled by `LIGHTING_COMPOSITE_EXECUTOR` with five independent conditions:
1. LED fixtures;
2. floodlights on lighting masts;
3. console fixtures on supports;
4. explicit proof that the remaining territory is illuminated by console fixtures on supports;
5. addressable adoption of SP 52.13330.2016 for artificial-lighting levels.

Current Test 78 evidence proves conditions 1, 2, 3 and 5. The project text/graphics show masts in the central area and console fixtures on supports, but do not textually prove that **all remaining territory** is covered by that solution. Therefore row 39 must remain review-only at **4/5** until a spatial/drawing proof is available.

This is an intentional false-positive safeguard.

### Power supply — diagnostic correction

The previous 5/8 audit was too conservative because IOS1.2 graphical evidence explicitly shows overhead-line supports on concrete footings. Current evidence status is therefore **6/8**.

The requirement remains review-only because:
- DGS is addressably tied to the special group of category I (plus administrative buildings), not proven for the Assignment's broader category-I formulation;
- PUE has addressable application evidence;
- FNP No. 505 is still found only in the normative bibliography, not in an addressable engineering-adoption statement.

### Other audited candidates

- DSK 500 t/h + two lines: two parallel/identical lines are proven, but an addressable project value of total 500 t/h has not been found; do not infer it from individual equipment capacities.
- Assignment transport wording (SinoTrack 42 t / 32 m3): current TH contains SINOTRUK/HOWO transport references, but the exact 42 t / 32 m3 characteristics were not addressably recovered from the benchmark source; no new deviation is accepted.
- Lime-supply canopy pos. 4.25: the canopy itself is proven, but the explicit **open** characteristic has not yet been textually proven; do not close the requirement from the word `навес` alone.

### Validation infrastructure

A direct branch validation workflow was added at `.github/workflows/validate-252.yml`.
It is designed to run:
- `pytest -q tests/core25/test_coverage_breakthrough_252.py`;
- `pytest -q tests/core25 --ignore=tests/core25/test_assignment_pipeline.py`;

and persist the validated source SHA into `checkpoints/252_validation/LAST_GREEN.md` after success.

At this checkpoint the marker has not appeared through connector-generated pushes, so no green CI result is claimed. An isolated logic harness reproduces the intended safety behavior (row 39 = 4/5, row 40 = 5/5), but this does **not** replace the required full repository regression.

### Next step

1. obtain a full regression/benchmark execution on the current branch;
2. if green and Test 78 reproduces row 40 as categorical with no regressions, promote the baseline from 21/56 to 22/56;
3. then continue with the next `PROFILE_SECTION_PRESENT` candidate, prioritizing simple addressable requirements before larger composite/NTD cases.
