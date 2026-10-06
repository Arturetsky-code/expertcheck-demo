# ExpertCheck development state

Updated: 2026-09-24
Active branch: `codex/expertcheck-25.2-coverage-breakthrough`
Latest validated source commit: `647291933d2b48fe84318891a2845c5e4cb01008`
Green validation marker commit: `ecfb2e432e2b0c43e545d268643793c07562468b`

## Official accepted local checkpoint

Assignment compliance / Test 78 / AI off:

- Requirements: 56
- `Соответствует заданию`: 24
- Proven deviations: 2
- `Требует проверки`: 30
- Strict categorical coverage: **26/56 = 46.4%**
- Admission diagnostics include **PROFILE_SECTION_ABSENT**
- Test 78 count at PROFILE_SECTION_ABSENT: **15 requirements**

Accepted categorical deviations:
- Requirement 22: loader identity/quantity mismatch.
- Requirement 3: Appendix 1 identification responsibility mismatch for exact GP position **4.25 “Навес системы подачи извести”**: Assignment **КС-2, γn=1.0** vs KR **КС-3, γn=1.1**.

Previously accepted compliance at 21/56:
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

Official accepted benchmark remains **Test 78 = 21/56 (37.5%)**.

### A/B correction — lightning/grounding is not a new coverage gain

The real 12-file Test 78 package was recovered from the Library and a fast deterministic
Assignment-only benchmark path was reproduced on the same 56 extracted requirements.

A/B against the last materialized source point before today's row-39/40 work
(`57431b9affec5f9015b2f93d79cda97389489019`) showed:
- pre-WIP Core25: 19 `VERIFIED_OK`, 37 `REVIEW_QUESTION`;
- current source: 19 `VERIFIED_OK`, 37 `REVIEW_QUESTION`;
- row 40 “Молниезащита и заземление” was already `VERIFIED_OK` before today's changes.

Therefore row 40 must **not** be counted as 22/56. Today's work hardened routing,
scope and regression protection but produced no accepted coverage increase.

### Electrical lighting — deliberately held at 4/5

Requirement row 39 remains review-only. The project proves:
1. LED fixtures;
2. floodlights on lighting masts;
3. console fixtures on supports;
4. addressable adoption of SP 52.13330.2016.

The project does not yet prove the literal full condition that all **remaining territory**
is illuminated by console fixtures on supports. The strict composite checker therefore
keeps the result at 4/5 and prevents a false positive.

### Power supply — diagnostic correction

Row 38 is now audited at **6/8** rather than 5/8 because IOS1.2 graphical evidence
explicitly shows overhead-line supports on concrete footings.

The row remains review-only because:
- DGS is addressably tied to the special group of category I (plus administrative buildings),
  not proven for the Assignment's broader category-I wording;
- PUE has addressable application evidence;
- FNP No. 505 is still present only in the normative bibliography, without an addressable
  engineering-adoption statement.

### Validation state

Current branch point `883fe8b4a6f0b6d49877b85bc26828a01e7be8b6` is green in both:
- `Core25 Quality Leap gates`;
- `Validate ExpertCheck 25.2 branch`.

The direct validation workflow now mirrors the proven Core25 pytest invocation.

### Real Test 78 package

The recovered benchmark archive `Комплект(2).zip` contains exactly the 12 expected
DSK PDFs. The deterministic Assignment contour extracts exactly 56 requirements.

A full `analyze_uploaded` run remains expensive and was not accepted from a partial
62% execution. For development A/B, the fast path reuses the same Assignment
extraction/evidence-admission/Core25 code while excluding unrelated heavy report/NTD stages.

### Next experiment — Drawing Intelligence / open canopy

The next evidence-near candidate is row 28:
`Навес системы подачи извести (поз. 4.25) выполнить открытым`.

Text alone proves the canopy but not the qualifier “open”. AR2/KR2 drawings provide
owner-bound facade/section/frame evidence. The next change must implement a reusable,
fail-closed drawing proof that requires positive open-frame semantics plus exact owner
binding; the word “навес” alone must never prove openness.

The larger lime-supply-system requirement remains review-only because the Assignment
requires MКР volume 1 m3 while the project currently proves 1000 kg, not 1 m3.

\n\n## Validated checkpoint — 22/56 open-canopy drawing proof

Accepted Test 78 / Assignment compliance / AI off baseline is now **22/56 = 39.3%**:

- requirements: **56**;
- `Соответствует заданию`: **20**;
- proven deviations: **2**;
- `Требует проверки`: **34**.

### New accepted categorical requirement

Requirement `ASSIGN-618EAB7B243E86`:
`Навес системы подачи извести (поз. 4.25) выполнить открытым`.

Previous state: `REVIEW_QUESTION`.
Validated state: `VERIFIED_OK`.
Core25 proof: `PROVEN_MATCH / ASSIGNMENT_PRESENCE_CONFIRMED`.
Executor: `OPEN_CANOPY_DRAWING_EXECUTOR`.

Addressable drawing evidence:
- AR2, page 33, exact owner `Навес системы подачи извести`, position **4.25**;
- three facade directions plus section view;
- profiled roof decking is explicitly present;
- KR2, page 172 independently corroborates columns / vertical bracing and roof beams / purlins.

### A/B benchmark

The same cached Test 78 page corpus and the same 56 extracted Assignment requirements were run through the deterministic Assignment evidence/admission/Core25 contour.

Control source before the open-canopy experiment:
- **19 VERIFIED_OK / 37 REVIEW_QUESTION**.

Validated open-canopy source:
- **20 VERIFIED_OK / 36 REVIEW_QUESTION**.

Exactly one requirement changed state:
- `ASSIGN-618EAB7B243E86`: `REVIEW_QUESTION -> VERIFIED_OK`.

The two previously accepted categorical deviations are unchanged, so official strict categorical coverage moves from:
- **19 compliant + 2 deviations = 21/56**
to:
- **20 compliant + 2 deviations = 22/56**.

### False-positive safeguards

The new drawing proof is fail-closed:
- the word `навес` alone never proves openness;
- exact drawing position and title-block owner are required;
- the title-block owner must also be explicitly named by the Assignment requirement;
- drawing index / `Ведомость документов графической части` pages are excluded from proof;
- sheet titles such as `Фасады`, `Разрез`, `План`, `Схема` cannot become object owners;
- explicit wall/enclosure markers such as wall panels / sandwich panels block the open-canopy proof;
- AR facade/section semantics require at least three facade directions plus a section and roof solution;
- independent KR frame corroboration is mandatory;
- the executor runs only for atomic `PRESENCE_REQUIREMENT` rows and cannot intercept the larger composite lime-supply requirement.

### Validation

Validated source/control commit:
`a1855a657fcf069a6ab377578248edde2da61647`.

Direct validation:
- coverage-breakthrough regression: **passed**;
- Core25 regression package: **passed**;
- green marker commit: `aab7ac19d96e163e5cad6e4bfda33aea2723510b`.

Core25 Quality Leap:
- Core25 tests: **passed**;
- Core20 regression: **passed**;
- mandatory focused regressions: **passed**;
- legacy full repository suite against baseline allowlist: **passed**;
- Core25 compile: **passed**.

### Unchanged near candidates

- Electrical lighting remains **4/5** and review-only.
- Power supply remains **6/8** and review-only.
- The larger lime-supply-system requirement remains review-only because the Assignment requires MКР volume **1 m3**, while the project currently proves **1000 kg**, not the required volume.

### Next step

Continue only from the **22/56** baseline. Prioritize the next `PROFILE_SECTION_PRESENT` requirement where an addressable project fact exists but the proof route is missing. Do not weaken partial-condition gates to chase coverage.



## Validated checkpoint — 23/56 fencing composite proof

Accepted Test 78 / Assignment compliance / AI off baseline is now **23/56 = 41.1%**:

- requirements: **56**;
- `Соответствует заданию`: **21**;
- proven deviations: **2**;
- `Требует проверки`: **33**.

### New accepted categorical requirement

Requirement `ASSIGN-D068822E25D0D3`:
`Предусмотреть ограждение части площадки ... ворота и калитки ... размеры определить проектом ... ограждение принять заводского изготовления`.

Previous state: `REVIEW_QUESTION`.
Validated state: `VERIFIED_OK`.
Core25 proof: `PROVEN_MATCH / ASSIGNMENT_PRESENCE_CONFIRMED`.
Executor: `FENCING_COMPOSITE_EXECUTOR`.

The atom is now correctly classified as `PRESENCE_REQUIREMENT`; the secondary phrase
`требований нормативной документации` no longer reroutes the whole engineering requirement
to `NORMATIVE_COMPLIANCE`.

### Six-condition proof gate

Categorical proof requires all six conditions:

1. DSK territory is fenced;
2. vehicle gates are provided;
3. personnel wickets are provided;
4. gate/wicket dimensions are defined by the project;
5. the transport/normative sizing basis is present (design vehicle + SP 37.13330.2012 / carriageway sizing);
6. the fencing is factory-manufactured.

Addressable evidence:
- PZU1 page 27: DSK fencing, vehicle gates and 4.5 m gate widths;
- PZU2 page 5: wicket is explicitly present in the plan legend;
- PZU1 page 30: SP 37.13330.2012 carriageway sizing and the design HOWO T5G 30/50 t vehicles;
- KR1 page 68: mesh metal fencing panels are explicitly **factory-manufactured**;
- KR2 page 168: wicket 1500x2500 and gates are explicitly marked as complete-supply items.

### A/B benchmark

The same 56 Test 78 requirements and cached page corpus were run through the deterministic
Assignment evidence/admission/Core25 contour.

Before fencing work:
- **20 VERIFIED_OK / 36 REVIEW_QUESTION**.

Validated fencing source:
- **21 VERIFIED_OK / 35 REVIEW_QUESTION**.

Exactly one requirement changed state:
- `ASSIGN-D068822E25D0D3`: `REVIEW_QUESTION -> VERIFIED_OK`.

The two previously accepted deviations are unchanged, so official strict categorical coverage moves:
- **20 compliant + 2 deviations = 22/56**
to:
- **21 compliant + 2 deviations = 23/56**.

### False-positive safeguards

- the generic word `нормативн...` is not globally downgraded; the classifier exception is limited to
  composite fencing atoms containing fencing + gates + wickets;
- truly normative requirements such as dynamic-load foundation requirements remain
  `NORMATIVE_COMPLIANCE`;
- partial fencing evidence never becomes `verified_candidate`;
- missing factory-manufacture evidence keeps the result review-only;
- missing wicket or wicket dimension keeps the result review-only;
- the transport/normative basis is a separate required slot rather than inferred from gate width alone.

### Validation

Validated source commit:
`5af8867756b8edd025f3bd30f55c6e64b820eadb`.

Green validation marker:
`3f2d0dead0e7bedd8f70754467a19265a7bdca48`.

CI:
- `Core20 quality gates`: **success**;
- `Core25 Quality Leap gates`: **success**;
- `Validate ExpertCheck 25.2 branch`: **success**;
- source snapshot: **success**.

### Continue from here

Official next baseline is **23/56**.
Do not revisit the fencing result unless a regression appears.
Continue with the next `PROFILE_SECTION_PRESENT` review-only requirement using the same
rule: complete material-condition proof first, categorical admission only second.


## Validated checkpoint — 24/56 landscaping design proof

Accepted Test 78 / Assignment compliance / AI off baseline is now **24/56 = 42.9%**:

- requirements: **56**;
- `Соответствует заданию`: **22**;
- proven deviations: **2**;
- `Требует проверки`: **32**.

### New accepted categorical requirement

Requirement `ASSIGN-B52474791A34FB`:
source row 48 / landscaping and site-planning requirements.
Assignment instruction: `Определить при разработке документации`.

Previous state: `REVIEW_QUESTION`.
Validated state: `VERIFIED_OK`.
Type: `DESIGN_DETERMINED`.
Core25 proof: `PROVEN_MATCH / ASSIGNMENT_DESIGN_VALUE_CONFIRMED`.
Executor: `LANDSCAPING_DESIGN_DETERMINED_EXECUTOR`.

### Three-condition proof gate

Categorical proof requires all three independent PZU conditions:

1. textual project solution:
   `Описание решений по благоустройству территории` and an explicit statement that the DSK territory is landscaped;
2. graphical project solution:
   `План благоустройства М 1:1000`;
3. concrete implemented elements:
   surfacing / pedestrian paths plus small architectural forms (bins / benches).

Addressable evidence:
- PZU1 page 27: dedicated landscaping-solutions section and explicit project statement;
- PZU2 page 5: landscaping plan, surface schedule, pedestrian paths, small architectural forms, bins and benches.

### Classification / route correction

`Определить при разработке документации` is now treated as a true design-determined instruction
when it is not preceded by a primary engineering action.
The landscaping source-row title routes expected evidence to `ПЗУ`.

This does not change composite requirements where an earlier primary action exists
(e.g. `Предусмотреть ... определить размеры проектом` stays PRESENCE).

### A/B benchmark

The same cached Test 78 page corpus and the same 56 extracted Assignment requirements were used.

Before landscaping work:
- **21 VERIFIED_OK / 35 REVIEW_QUESTION**.

Validated landscaping source:
- **22 VERIFIED_OK / 34 REVIEW_QUESTION**.

Exactly one requirement changed state:
- `ASSIGN-B52474791A34FB`: `REVIEW_QUESTION -> VERIFIED_OK`.

The two accepted deviations are unchanged, so official strict categorical coverage moves:
- **21 compliant + 2 deviations = 23/56**
to:
- **22 compliant + 2 deviations = 24/56**.

### False-positive safeguards

- a generic mention of landscaping is insufficient;
- textual PZU evidence alone is insufficient;
- a drawing title alone is insufficient;
- categorical admission requires text + graphic plan + concrete project elements;
- partial 1/3 or 2/3 evidence remains candidate-only;
- only the explicit development-determined instruction is reclassified;
- ordinary composite engineering requirements remain on their original route.

### Validation

Validated source commit:
`0013ba07a409cef81f117ececcb5489130f50722`.

Green validation marker:
`f817001a295a29dcb07d847565870a94fad3ff9c`.

CI:
- `Core20 quality gates`: **success**;
- `Core25 Quality Leap gates`: **success**;
- `Validate ExpertCheck 25.2 branch`: **success**;
- source snapshot: **success**.

### Continue from here

Official next baseline is **24/56**.
Continue with the next review-only requirement only after an addressable evidence audit;
do not weaken the known water / automation / power / lighting condition gates.


## Validated checkpoint — 25/56 named-norm design adoption

Accepted Test 78 / Assignment compliance / AI off baseline is now **25/56 = 44.6%**:

- requirements: **56**;
- `Соответствует заданию`: **23**;
- proven deviations: **2**;
- `Требует проверки`: **31**.

### New accepted categorical requirement

Requirement `ASSIGN-6D099E6177F344`:
`Инженерную подготовку территории предусмотреть в соответствии с СП 45.13330.2017 ...`

Previous state: `REVIEW_QUESTION`.
Validated state: `VERIFIED_OK`.
Core25 proof:
- `PROVEN_MATCH`;
- `ASSIGNMENT_NORMATIVE_DESIGN_ADOPTION_CONFIRMED`;
- executor `NORMATIVE_DESIGN_ADOPTION_EXECUTOR`.

Proof is intentionally two-slot:
1. **DESIGN_SOLUTION** — PZU contains an addressable engineering-preparation solution for the site;
2. **NORMATIVE_ADOPTION** — the same Assignment-named norm is addressably adopted for the relevant earthwork/foundation works.

This proves transfer of the Assignment requirement into the PD. It does **not** assert full technical compliance with SP 45.13330.2017; that remains an NTD-contour task.

### A/B benchmark

Using the same cached real Test 78 page corpus and the same 56 extracted Assignment requirements:

- validated 24/56 baseline: **22 VERIFIED_OK / 34 REVIEW_QUESTION**;
- new source: **23 VERIFIED_OK / 33 REVIEW_QUESTION**.

Exactly one requirement changed categorical state:
- `ASSIGN-6D099E6177F344`: `REVIEW_QUESTION -> VERIFIED_OK`.

No other requirement changed state.

### False-positive safeguards

- a normative citation alone cannot close the requirement;
- a design solution without the Assignment-named norm cannot close it;
- all norms explicitly named by the Assignment must be addressably covered;
- generic bibliography/reference-list occurrences are insufficient;
- the project solution and normative adoption remain separate proof slots;
- Core25 requires both slots before categorical admission;
- full normative compliance is explicitly marked as **not assessed** by this proof.

### Validation

Validated source commit:
`fded177104b8527978ea7431873e9b99b3a7a768`.

Green direct-validation marker:
`9e82f3fbd66bc005164a380eeece825507624928`.

Passed:
- coverage-breakthrough regression;
- full Core25 regression package;
- Core25 Quality Leap tests;
- Core20 regression;
- baseline full diagnostic;
- mandatory focused regressions;
- legacy full repository suite against baseline allowlist;
- Core25 compile.

### Rejected WIP immediately before this checkpoint

A separate `STOCKPILE_COMPLEX_ACCESS_EXECUTOR` experiment was removed.
The stockpile-to-technological-complex access requirement was already
`VERIFIED_OK` at the 24/56 baseline via the existing
`PERSONNEL_AND_VEHICLE_ACCESS` executor. A/B showed **zero** benchmark gain,
and the duplicate route caused competing tests. The experiment was therefore
reverted rather than retained as architectural clutter.

### Next candidate

Requirement `ASSIGN-38E7D1D078444D`:
`Основания для установки технологического оборудования дробильного комплекса выполнить согласно нормативным требованиям к основаниям технологического оборудования с динамическими нагрузками`.

Current evidence is strong:
- KR1 develops foundations for the crushing equipment;
- KR1 explicitly applies SP 26.13330.2012 `Фундаменты машин с динамическими нагрузками`;
- KR1 provides calculated vibration amplitude **0.1 mm** versus allowable **0.3 mm**;
- KR2 contains the corresponding foundation layouts.

Because the Assignment does not name a specific norm, this requirement must use a stricter generic-normative proof than the named-norm executor above.



## Validated checkpoint — 26/56 dynamic machine foundations

Accepted Test 78 / Assignment compliance / AI off baseline is now **26/56 = 46.4%**:

- requirements: **56**;
- `Соответствует заданию`: **24**;
- proven deviations: **2**;
- `Требует проверки`: **30**.

### New accepted categorical requirement

Requirement `ASSIGN-38E7D1D078444D`:
`Основания для установки технологического оборудования дробильного комплекса выполнить согласно нормативным требованиям к основаниям технологического оборудования с динамическими нагрузками`.

Previous state: `REVIEW_QUESTION`.
Validated state: `VERIFIED_OK`.

Executor:
`DYNAMIC_FOUNDATION_NORMATIVE_EXECUTOR`.

Core25:
- proof state: `PROVEN_MATCH`;
- reason: `ASSIGNMENT_DYNAMIC_FOUNDATION_NORMATIVE_CONFIRMED`.

### Four-condition proof gate

Categorical proof requires all four independent elements:

1. the PD actually develops foundations for crushing-process equipment;
2. the PD addressably adopts the specialized `СП 26.13330.2012 «Фундаменты машин с динамическими нагрузками»`;
3. a quantitative dynamic calculation proves the calculated vibration amplitude does not exceed the stated allowable limit;
4. KR graphical documentation independently shows the corresponding foundation plates.

Real Test 78 evidence:
- KR1 page 74: foundations for modular crushing installations are developed;
- KR1 page 74: SP 26.13330.2012 is addressably applied;
- KR1 page 74: calculated foundation vibration amplitude **0.1 mm** does not exceed allowable **0.3 mm**;
- KR2 page 31: foundation-plate layout `ФПм1 / ФПм2 / ФПм3` for crushing-complex equipment.

### A/B benchmark

Using the same cached real Test 78 page corpus and the same 56 extracted Assignment requirements:

- validated 25/56 baseline: **23 VERIFIED_OK / 33 REVIEW_QUESTION**;
- dynamic-foundation source: **24 VERIFIED_OK / 32 REVIEW_QUESTION**.

Exactly one requirement changed state:
- `ASSIGN-38E7D1D078444D`: `REVIEW_QUESTION -> VERIFIED_OK`.

The two previously accepted proven deviations are unchanged. Therefore official strict coverage moves from:
- **23 compliant + 2 deviations = 25/56**
to:
- **24 compliant + 2 deviations = 26/56**.

### False-positive safeguards

The proof remains fail-closed:
- SP 26 appearing only in a bibliography / normative list is insufficient;
- a foundation solution without a quantitative dynamic calculation is insufficient;
- a calculation without an addressable foundation drawing is insufficient;
- a drawing without the calculation is insufficient;
- calculated vibration exceeding the stated allowable limit cannot produce compliance;
- full compliance with every clause of SP 26.13330.2012 is **not** asserted by this Assignment proof.

### Validation

Validated source commit:
`647291933d2b48fe84318891a2845c5e4cb01008`.

Green validation marker:
`ecfb2e432e2b0c43e545d268643793c07562468b`.

Passed:
- direct coverage-breakthrough regression;
- full Core25 regression package;
- Core25 Quality Leap tests;
- Core20 regression;
- baseline full diagnostic;
- mandatory focused regressions;
- legacy full repository suite against baseline allowlist;
- Core25 compile.

### Continue from here

Official next baseline is **26/56**.

Do not revisit:
- stockpile-to-technological-complex access — already covered by `PERSONNEL_AND_VEHICLE_ACCESS`;
- climate II4 — no project-side II4 evidence in the 12-file benchmark;
- block-modular characteristics per manufacturer documentation — sufficient project-side declaration not found.

Continue with the next genuinely review-only `PROFILE_SECTION_PRESENT` requirement and preserve the same A/B + false-positive audit discipline.


## Test78 deterministic A/B automation — ready, secret activation pending

A dedicated workflow now exists at:
`.github/workflows/test78-ab.yml`.

Runner:
`tools/run_test78_ab.py`.

Security model:
- repository visibility is **public**;
- the real Test78 fixture is therefore stored only as AES-256-CBC + PBKDF2 encrypted ciphertext chunks under `knowledge/benchmarks/private/`;
- plaintext project-page text, source PDFs and the decryption key are not committed;
- workflow output contains only counts, changed requirement IDs and Core25 reason/executor identifiers.

Fixed encrypted fixture baseline:
- Test78 denominator: **56** requirements;
- baseline Core25: **24 VERIFIED_OK / 32 REVIEW_QUESTION**;
- separately audited proven deviations: **2**;
- official strict categorical baseline: **26/56 = 46.4%**;
- baseline source SHA: `647291933d2b48fe84318891a2845c5e4cb01008`.

A local encrypted-fixture smoke test reproduced:
- fixture decrypt exact-match: **yes**;
- classification: `NO_CHANGE`;
- current Core25: **24 VERIFIED_OK / 32 REVIEW_QUESTION**;
- changed requirements: **0**.

Workflow behavior:
- `NO_CHANGE`: no benchmark state change;
- `SINGLE_GAIN`: exactly one review-only requirement became VERIFIED_OK;
- `MULTI_CHANGE_AUDIT_REQUIRED`: multiple changes require manual evidence audit;
- `REGRESSION`: workflow fails closed;
- `REQUIREMENT_SET_CHANGED`: workflow fails closed.

Activation requirement:
repository Actions secret `TEST78_FIXTURE_KEY` must be configured once.
Until then the workflow completes successfully but deliberately skips decryption/benchmark execution.

After activation, development A/B no longer requires downloading source ZIP artifacts or rebuilding the 12-PDF page corpus for each iteration.


## Current validated checkpoint — 25/56 after false-positive correction

This section supersedes the previous **26/56** checkpoint as the current accepted
Test78 / Assignment compliance / AI-off baseline. The earlier checkpoint remains above
as development history.

Current strict categorical baseline:
- requirements: **56**;
- `VERIFIED_OK`: **23**;
- separately audited proven deviations: **2**;
- `REVIEW_QUESTION`: **33**;
- official strict categorical coverage: **25/56 = 44.6%**.

### Why the baseline decreased from 26/56

A false-positive proof was found for requirement `ASSIGN-4F91A035979A30`.
The requirement is a non-numeric `PRESENCE_REQUIREMENT`, but atomisation had retained
a secondary `parameter_code=VOLUME`. The generic directed-value retriever therefore
admitted unrelated project volume values as evidence for the presence requirement.

The correction is intentionally universal:
- numeric directed evidence is now produced only for explicit `VALUE_COMPARISON`
  requirements;
- inherited secondary parameter codes no longer override semantic section routing for
  presence/normative atoms;
- two regression tests protect both behaviours.

Exactly one Test78 requirement changed during the correction:
- `ASSIGN-4F91A035979A30`: `VERIFIED_OK -> REVIEW_QUESTION`.

The other **55/56** requirement states remained unchanged. This is an accepted quality
correction, not a capability gain/loss experiment.

### Universal-archetype coverage

The validated `VERIFIED_OK` set is currently explained by **11 reusable requirement
archetypes**:
- **23/23** verified requirements are mapped to a universal archetype;
- **0** verified requirements remain unclassified.

This metric is now reported by deterministic Test78 alongside categorical coverage.
Development must prefer improving/reusing an archetype over adding a one-off executor
for a single benchmark sentence.

### Test78 automation state

The GitHub Actions secret is configured and the deterministic workflow is **active**.
The previous “secret activation pending” note is historical.

The fixed encrypted Test78 corpus remains private ciphertext in the public repository.
Validated baseline state is now separated from the encrypted corpus through:
`knowledge/benchmarks/test78_baseline_overrides.json`.

This avoids rebuilding/re-encrypting the 956-page corpus for every audited baseline
correction while keeping project text out of public Git history.

An encrypted private review-frontier artifact is also produced for diagnostics.
The public compact A/B result contains only non-sensitive counts, requirement IDs,
structural diagnostics and reason/executor identifiers.

### Validation

Quality correction commit:
`af9b1d6cf73e9dbfb176b85287b9de76ace63533`.

Corrected Test78 baseline commit:
`3cfd66be54bd4eae187752a6bd80618ed06f387b`.

GitHub validation at the corrected baseline:
- Test78 deterministic A/B: **success / NO_CHANGE**;
- Core20 quality gates: **success**;
- Core25 Quality Leap gates: **success**;
- Source Snapshot Artifact: **success**.

### Review-frontier finding

The strongest remaining review candidates were audited without weakening proof gates.
Several are evidence-limited by the current 12-document benchmark rather than by a
missing executor. Examples include partial multi-condition normative, lighting,
water/sewer, equipment-parameter and cross-document requirements.

Do not force a new categorical result merely to restore **26/56**.

### Continue from here

1. Treat **25/56** as the only current accepted Test78 baseline.
2. Use the review frontier to distinguish:
   - an existing archetype with a routing/admission defect;
   - a genuinely new reusable archetype;
   - a requirement that cannot be proven from the current corpus.
3. Add a new executor only when it represents a reusable engineering proof pattern,
   never solely to close one Test78 sentence.
4. Preserve fail-closed evidence rules and accept a lower benchmark percentage when it
   removes a false positive.

## Validated checkpoint — native Core25 equipment mismatch proof

The strict Test78 baseline remains **25/56 = 44.6%**, but one of the two
previously external/manual deviations is now proven inside the Core25 pipeline.

### Runtime result

Requirement `ASSIGN-F53C5BA692BD3F`:
`Подача руды в приёмный бункер осуществляется двумя погрузчиками SHANTUI L76-С5 ...`

Previous Core25 state:
- `REVIEW_QUESTION / INSUFFICIENT`;
- the legacy deterministic executor already reported a deviation, but Core25 rejected
  the evidence because exact owner equality was required before mismatch proof.

Validated Core25 state:
- `PROJECT_FINDING`;
- proof: `PROVEN_MISMATCH`;
- reason: `EQUIPMENT_IDENTITY_OR_QUANTITY_MISMATCH`;
- executor/archetype: `EQUIPMENT_IDENTITY_AND_QUANTITY`.

The project equipment register proves **4 loaders** while the Assignment requires
**2 loaders**. This strong quantity mismatch is sufficient for a categorical deviation.
The differing manufacturer/brand is retained as diagnostic evidence but is not required
for the categorical result.

### Universal false-positive guard

The new route is not tied to DSK or to a concrete model name.

Core25 may bind a mismatch candidate to the requirement comparison subject only when:
1. the candidate comes from the trusted `EQUIPMENT_REGISTER_COMPARISON` route;
2. the equipment role itself is proven;
3. the evidence is addressable/canonical;
4. a strong mismatch is proven in **model or quantity**.

A manufacturer/brand spelling difference by itself is deliberately insufficient.
The neighbouring SinoTrack / SINOTRUK truck requirement therefore remains
`REVIEW_QUESTION`.

### Deterministic Test78 A/B

Source commit:
`7cd5779af03e1939cb89381aeed7dbf04fc2b5b0`.

Exactly one requirement changed:
- `ASSIGN-F53C5BA692BD3F`: `REVIEW_QUESTION -> PROJECT_FINDING`.

No `VERIFIED_OK` requirement regressed and no second requirement became categorical.

### Baseline accounting

The baseline manifest now treats the loader finding as a native Core25 result:
- `VERIFIED_OK`: **23**;
- native `PROJECT_FINDING`: **1**;
- separately audited external deviations: **1**;
- `REVIEW_QUESTION`: **32**;
- strict categorical coverage: **25/56**.

This is not a percentage gain. It is an architectural quality gain: one manually
maintained exception has been replaced by a reusable auditable proof route.

### Continue from here

Continue from the review frontier. Prefer:
- reusable routing/binding/proof defects;
- native migration of the remaining external deviation when a general proof pattern
  can be established;
- genuine new archetypes only when the current corpus contains complete addressable
  evidence.

Do not promote brand-only equipment differences or incomplete composite requirements.

## Validated quality checkpoint — local identification-record binding

The experimental identification-attribute proof that initially produced a new
`PROJECT_FINDING` on positions **4.2.1** and **4.4** was not accepted into the
baseline.

Root cause:
- `identity_context()` previously used a broad ±700-character window around an exact
  position;
- dense identification tables can place several neighbouring object rows inside that
  window;
- responsibility class / reliability coefficient could therefore be borrowed from an
  adjacent row.

Universal correction:
- identification attributes are now bound to the same local position/object record;
- multiline tables stop at the next distinct dotted GP position;
- flattened PDF text falls back to an exact-position span ending at the next distinct
  position;
- records containing conflicting identification values are fail-closed;
- regression tests cover adjacent rows and flattened-table extraction.

Validated correction source:
`92430eb9612afbe079552fb78d2ed74ae5610aa3`.

Green validation marker:
`9c581a4dc7bd44e1be588a461e1ea89d2acb22b3`.

Validation:
- Test78 deterministic A/B: **success / NO_CHANGE**;
- changed requirement IDs: **0**;
- Core20 quality gates: **success**;
- Core25 Quality Leap gates: **success**;
- Validate ExpertCheck 25.2 branch: **success**;
- Source Snapshot Artifact: **success**.

Current accepted baseline remains:
- **23 VERIFIED_OK**;
- **1 native PROJECT_FINDING**;
- **1 separately audited external deviation**;
- **32 REVIEW_QUESTION**;
- strict categorical coverage: **25/56 = 44.6%**;
- **12** universal archetypes across native categorical results.

The capacity/topology frontier candidate remains review-only by design:
`NOMINAL_TOTAL_CAPACITY` in the Assignment is not semantically equivalent to the
project evidence classified as `OPERATING_SECTION_THROUGHPUT`.

### Continue from here

Do not revisit the rejected 4.2.1 / 4.4 identification findings.

Next preferred direction:
1. preserve the corrected local-record identification binding;
2. inspect the remaining separately audited identification deviation and determine
   whether the exact expected/project position record can be represented by the same
   reusable identification archetype;
3. do not force capacity/topology comparison across incompatible semantic levels;
4. accept no baseline change without deterministic Test78 A/B and false-positive audit.

## Validated checkpoint — all audited deviations native in Core25

Requirement `ASSIGN-1C2C21F3A4BBF3` is now closed as a native Core25
`PROJECT_FINDING`.

Validated identification mismatch:
- exact GP position: **4.25**;
- Assignment: **КС-2**;
- project KR identification table: **КС-3**;
- proof: `PROVEN_MISMATCH`;
- reason: `IDENTIFICATION_ATTRIBUTE_MISMATCH`;
- executor/archetype: `IDENTIFICATION_ATTRIBUTE_COMPARISON_EXECUTOR`.

The proof does not use broad text windows. It is admitted only after a strict
columnar-table contract:
1. canonical KR page;
2. exact unique GP positions;
3. exact unique full object names;
4. identical position and owner ordering;
5. responsibility-class vector cardinality exactly equals matched row cardinality;
6. Assignment-side identification attributes were independently addressable;
7. only the row-level difference is promoted.

For the decisive project page the aligned vector is:
- 4.24 → КС-2;
- 4.25 → КС-3;
- 4.26 → КС-2.

The corresponding Assignment page maps:
- 4.24 → КС-2;
- 4.25 → КС-2;
- 4.26 → КС-2.

Deterministic Test78 A/B at source commit
`8ec4d92a5346339a92b20ac368eb0048fc634bd9` changed exactly one requirement:
- `ASSIGN-1C2C21F3A4BBF3`: `REVIEW_QUESTION -> PROJECT_FINDING`.

Validation at that commit:
- Test78 deterministic A/B: **success / CHANGE_AUDIT_REQUIRED** with exactly one audited change;
- Core20 quality gates: **success**;
- Core25 Quality Leap gates: **success**;
- Validate ExpertCheck 25.2 branch: **success**;
- Source Snapshot Artifact: **success**.

### Baseline accounting after native migration

The strict score remains **25/56 = 44.6%** because this requirement was already
counted as the one remaining separately audited external deviation.

New accounting:
- `VERIFIED_OK`: **23**;
- native `PROJECT_FINDING`: **2**;
- separately audited external deviations: **0**;
- `REVIEW_QUESTION`: **31**;
- strict categorical coverage: **25/56**;
- native categorical archetypes: **13**.

This is an architectural gain rather than a percentage gain: the benchmark no longer
depends on any manually maintained external deviation count.

### Continue from here

The next development cycle starts from a fully native 25/56 baseline.
Do not compare `NOMINAL_TOTAL_CAPACITY` with `OPERATING_SECTION_THROUGHPUT`.
Prefer the next review-only requirement where complete addressable evidence exists and
the improvement extends or reuses a general archetype.



## Validated checkpoint — fail-closed unrouted normative adoption (26/56)

Source code commit:
`ccb749b2477138d846ea5f69f2a5e80fa495076c`

Green regression marker:
`029975ec36d3ec0b690a00700ae2e644a0dbc897`

### Test78 result

Deterministic Test78 A/B produced **SINGLE_GAIN** with exactly one changed requirement:

- `ASSIGN-016FCF9FBA5CD6`: `REVIEW_QUESTION -> VERIFIED_OK`;
- proof: `PROVEN_MATCH`;
- reason: `ASSIGNMENT_NORMATIVE_DESIGN_ADOPTION_CONFIRMED`;
- executor/archetype: `NORMATIVE_DESIGN_ADOPTION_EXECUTOR` / `NORMATIVE_DESIGN_ADOPTION`.

New strict categorical accounting:
- `VERIFIED_OK`: **24**;
- native `PROJECT_FINDING`: **2**;
- `REVIEW_QUESTION`: **30**;
- external deviations: **0**;
- strict categorical coverage: **26/56 = 46.4%**;
- native categorical archetypes: **13**;
- all 26 categorical rows map to a native archetype.

This gain reuses the existing normative-design-adoption archetype; it does not add a
requirement-specific executor.

### Universal safeguard

The defect was an admission/routing gap for normative action requirements whose
`expected_sections` could not be inferred.

The accepted fallback is deliberately fail-closed:

1. when the requirement has no inferred profile sections, evidence may not be
   assembled from unrelated pages across the project;
2. one and the same addressable project page must prove the engineering subject and
   project/design assertion;
3. that same page must prove adoption of **every** normative reference explicitly named
   in the Assignment;
4. split-page evidence without an inferred route remains `REVIEW`;
5. `NORMATIVE_DESIGN_ADOPTION_EXECUTOR` may resolve an otherwise `UNRESOLVED`
   non-object scope to project-global only after the deterministic executor has produced
   the qualified proof package;
6. different proof roles on the same page are retained separately by including
   `evidence_kind` and `proof_slot` in both coverage deduplication and Core25 evidence
   identity.

This prevents a bibliography/reference-only hit or a norm found in one document plus an
unrelated design statement in another from becoming categorical.

### Validation

At source commit `ccb749b...`:
- Core25 Quality Leap gates: **success**;
- Core25 tests: **143 passed**;
- Core20 regression: **success**;
- Core20 quality gates: **success**;
- results integrity: **success**;
- Validate ExpertCheck 25.2 branch: **success**;
- Source Snapshot Artifact: **success**;
- Test78 deterministic A/B: **success / SINGLE_GAIN**.

### Continue from here

Treat **26/56** as the accepted baseline only after the baseline-manifest recheck returns
`NO_CHANGE`.

Do not promote:
- `ASSIGN-E9BD8EC7BDE545` across incompatible capacity semantic levels;
- `ASSIGN-15C37B5DD8F8C8` from a brand/manufacturer difference alone;
- `ASSIGN-56D65F62613D01` while the lighting composite remains incomplete.

Preferred next work is another review requirement where complete addressable evidence
already exists and the fix improves a reusable archetype rather than one Test78 ID.


## Validated checkpoint — high-confidence unsectioned presence (27/56)

Source code commit:
`3e2c23330e4233aed6c34cf58d2ab99fa3a20f07`

Green regression marker:
`7597e849ab5a1b1e3fd9fb833a0b025f5b7f5f0d`

### Test78 result

Deterministic Test78 A/B produced **SINGLE_GAIN** with exactly one changed requirement:

- `ASSIGN-1ABCB2369DD986`: `REVIEW_QUESTION -> VERIFIED_OK`;
- proof: `PROVEN_MATCH`;
- reason: `ASSIGNMENT_PRESENCE_CONFIRMED`;
- executor/archetype: `GENERIC_PRESENCE_EXECUTOR` / `PRESENCE`.

New strict categorical accounting:
- `VERIFIED_OK`: **25**;
- native `PROJECT_FINDING`: **2**;
- `REVIEW_QUESTION`: **29**;
- external deviations: **0**;
- strict categorical coverage: **27/56 = 48.2%**;
- native categorical archetypes: **13**;
- all 27 categorical rows map to a native archetype.

### Universal safeguard

The gap was generic presence requirements for which no profile section could be inferred.
The previous implementation required a non-empty section route even when the same PZ
page almost completely reproduced the engineering requirement.

The accepted fallback remains fail-closed.  An unsectioned presence requirement may be
promoted only when all of the following are true:

1. requirement type is `PRESENCE_REQUIREMENT`;
2. no expected section route exists;
3. the requirement is not object/equipment bound;
4. no numeric required value and no parameter code are present;
5. the requirement is an affirmative engineering action, not a negative/applicability
   statement;
6. the proof comes from one addressable `ПЗ` page;
7. the page contains an explicit project/design assertion;
8. every critical qualifier is present;
9. at least 8 significant requirement terms are present;
10. full semantic coverage is at least **0.85**.

The decisive Test78 candidate had **16/18 = 0.889** full term coverage.
Nearby review candidates remained below the threshold or failed qualifiers/owner/design
gates:
- `ASSIGN-4F91A035979A30`: 6/18, qualifiers incomplete, stale secondary parameter
  remains non-authoritative;
- `ASSIGN-ADC7788A7483F8`: 9/18;
- `ASSIGN-783AD352DCC283`: 5/10;
- object-bound candidates remain excluded.

Thus the gain does not reopen the previously corrected false-positive route for
`ASSIGN-4F91A035979A30`.

### Validation

At source commit `3e2c233...`:
- Test78 deterministic A/B: **success / SINGLE_GAIN**;
- Core25 Quality Leap gates: **success**;
- Core20 regression: **success**;
- Core20 quality gates: **success**;
- results integrity: **success**;
- Validate ExpertCheck 25.2 branch: **success**;
- Source Snapshot Artifact: **success**.

### Continue from here

Treat **27/56** as accepted only after the baseline-manifest recheck returns
`NO_CHANGE`.

Do not promote:
- capacity evidence across incompatible semantic levels;
- brand-only equipment differences;
- incomplete lighting/normative composites;
- object-bound or partial generic presence matches.

Preferred next work: inspect the remaining review frontier for a reusable evidence
contract or cross-document trace pattern with complete addressable evidence.


## Validated architecture checkpoint — fail-closed cross-document trace

Source code commit:
`dc62dc0537ec5598afa7861c83817116be5aaed4`

Green regression marker:
`b76ac0729a686458044da22cfd71389a432c27f7`

### Why this did not change Test78

The remaining Test78 `CROSS_DOCUMENT_TRACE` requirement
`ASSIGN-2C7DB91DFF4DA6` still correctly remains `REVIEW_QUESTION`.

Safe benchmark diagnostics prove that the current 12-document corpus contains:
- **0** source/survey pages matching the requirement;
- many project-design pages, but maximum design-side semantic coverage only **0.357**;
- therefore no two-sided source-input -> project-adoption chain exists in the fixture.

Test78 after the new route:
- classification: **NO_CHANGE**;
- `VERIFIED_OK`: **25**;
- native `PROJECT_FINDING`: **2**;
- `REVIEW_QUESTION`: **29**;
- strict categorical coverage: **27/56 = 48.2%**;
- changed IDs: **none**.

### New universal Core25 route

Core25 now supports `TRACEABILITY` instead of forcing all
`CROSS_DOCUMENT_TRACE` requirements into `REVIEW_ONLY`.

A categorical trace is admitted only when two independent, addressable evidence roles
are present:

1. `SOURCE_INPUT` — verified source/engineering-survey evidence;
2. `PROJECT_ADOPTION` — verified project statement showing that the source input was
   actually adopted.

Both evidence rows must:
- be `verified_candidate`;
- use `QUALIFIED_CROSS_DOCUMENT_TRACE`;
- declare `trace_chain=true`;
- share the same non-empty `trace_subject_key`;
- share the same non-empty `trace_anchor`;
- contain at least two matched semantic terms;
- come from **different documents**.

Additionally:
- source evidence must declare `source_input_verified=true`;
- project evidence must declare `project_adoption_verified=true`;
- project evidence must contain a project/design assertion.

Only then Core25 emits:
- `PROVEN_MATCH`;
- reason `ASSIGNMENT_CROSS_DOCUMENT_TRACE_CONFIRMED`;
- universal archetype `CROSS_DOCUMENT_TRACE`.

### Regression guards

Tests cover:
1. complete two-sided source -> project chain -> `VERIFIED_OK`;
2. missing source side -> `REVIEW`;
3. different trace anchors -> `REVIEW`;
4. same document used for both roles -> `REVIEW`.

### Validation

At source commit `dc62dc0...`:
- Test78 deterministic A/B: **success / NO_CHANGE**;
- Core25 Quality Leap gates: **success**;
- Core25 tests: **success**;
- baseline full diagnostic: **success**;
- Core20 regression: **success**;
- Core20 quality gates: **success**;
- results integrity: **success**;
- Validate ExpertCheck 25.2 branch: **success**;
- Source Snapshot Artifact: **success**;
- alpha1 release gate: **success**.

### Continue from here

The Test78 benchmark cannot validate the positive trace path until engineering-survey
source documents are added to a benchmark corpus.

Next development direction should therefore be one of:
- add a dedicated synthetic/expanded benchmark containing PD + engineering surveys and
  validate the new `TRACEABILITY` route end-to-end;
- continue the current 12-document review frontier only where complete evidence is
  actually present.

Do not turn a project-side statement alone into a cross-document proof.


## Validated traceability extension — raw corpus qualification

Source commits:
- `8c2a0ae7ca2907f3163a271e427d064133af7350` — explicit survey-to-project trace qualification;
- `5f3384f5a49e9cdda43fc97bfccce380afd320c0` — preserve engineering foundation subject semantics.

Green regression marker:
`790d157c97a41f95c1b199880f5da0054eb853f1`

### End-to-end behavior

The traceability path now works from raw page corpus, not only from pre-qualified
synthetic evidence.

For `CROSS_DOCUMENT_TRACE`, the deterministic checker may emit a verified two-role
package only when:

1. an addressable source page is recognized as an engineering-survey source;
2. an addressable project page contains an explicit adoption statement referring to
   engineering-survey results/materials;
3. both pages contain at least two specific engineering-subject terms from the
   Assignment requirement;
4. both pages contain the same explicit report/reference anchor extracted from a
   `Шифр ...`, `Отчет № ...` or equivalent identifier;
5. the shared anchor contains a sufficiently specific alphanumeric/reference token;
6. the source and project documents are distinct.

The checker then emits:
- `QUALIFIED_CROSS_DOCUMENT_TRACE / SOURCE_INPUT`;
- `QUALIFIED_CROSS_DOCUMENT_TRACE / PROJECT_ADOPTION`;
- the same `trace_subject_key` and `trace_anchor`;
- independently verified source/adoption flags.

Core25 then re-validates this package through the fail-closed `TRACEABILITY` proof.

### Important semantic correction

The first end-to-end implementation failed one regression test because stem
`основани` was incorrectly treated as generic wording from the phrase
`на основании`.

That is unsafe for engineering semantics because `основания зданий` is a real
engineering subject.

The accepted correction keeps foundation/base semantics as a subject term while
`на основании` remains an adoption relation detected separately.

### Regression coverage

The validated tests now cover:
- raw engineering-survey + project pages with the same report anchor -> categorical
  trace proof;
- missing source document -> `REVIEW`;
- mismatched explicit report anchors -> `REVIEW`;
- Core25 source-side missing -> `REVIEW`;
- Core25 mismatched anchors -> `REVIEW`;
- same document used as both trace roles -> `REVIEW`.

### Current Test78 accounting

No Test78 score change is accepted from this work:
- `VERIFIED_OK`: **25**;
- `PROJECT_FINDING`: **2**;
- `REVIEW_QUESTION`: **29**;
- strict categorical coverage: **27/56 = 48.2%**;
- Test78 classification after the final trace implementation: **NO_CHANGE**;
- changed requirement IDs: **none**.

The benchmark cannot exercise the positive trace path because the current 12-document
fixture contains **0 matching engineering-survey source pages**.

### Validation

At final source commit `5f3384f...`:
- Core25 Quality Leap gates: **success**;
- Core25 tests: **success**;
- baseline full diagnostic: **success**;
- Core20 regression: **success**;
- Core20 quality gates: **success**;
- results integrity: **success**;
- Validate ExpertCheck 25.2 branch: **success**;
- Source Snapshot Artifact: **success**;
- Test78 deterministic A/B: **success / NO_CHANGE**;
- alpha1 release gate: **success**.

### Continue from here

The next useful validation step for this archetype is a benchmark that actually contains
both PD and engineering-survey documents. Until then, do not relax the explicit
cross-document anchor requirement merely to move Test78.

For the current 12-document frontier, continue only with review requirements whose
complete evidence is actually present in the fixture.


## Validated checkpoint — review frontier audit and survey-discipline breadth

Traceability breadth source/test commit:
`58444629d46cb01d9fb805d0f6849e5bfd983ebb`

Green regression marker:
`09247d0b32a8da4d5ce96d7ba2f910cc90efc6d5`

### Cross-document trace is not geology-specific

The same deterministic `CROSS_DOCUMENT_TRACE` path is now regression-tested
end-to-end for four engineering-survey disciplines:

- ИГИ — engineering geology;
- ИГДИ — engineering geodesy;
- ИГМИ — engineering hydrometeorology;
- ИЭИ — engineering ecology.

Every positive test uses the same generic contract:
1. addressable survey source;
2. addressable project adoption statement;
3. shared explicit report/reference anchor;
4. shared engineering subject;
5. different source/project documents;
6. Core25 re-validation through `TRACEABILITY`.

No discipline-specific executor or DSK-specific requirement ID was added.

Validation at `5844462...`:
- Core25 tests: **success**;
- baseline full diagnostic: **success**;
- Core20 regression: **success**;
- Core20 quality gates: **success**;
- results integrity: **success**;
- Validate ExpertCheck 25.2 branch: **success**;
- Source Snapshot Artifact: **success**;
- alpha1 release gate: **success**.

### Current 12-document REVIEW frontier audit

The deterministic Test78 baseline remains **27/56 = 48.2%**
(`25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW`).

The remaining high-priority review candidates were explicitly audited:

- lighting composite `ASSIGN-56D65F62613D01`: only **2/5** slots are actually
  proven (`led_fixtures`, `sp52_adoption`); `floodlight_masts`,
  `console_fixtures`, and `territorial_layout` are absent;
- cross-document trace `ASSIGN-2C7DB91DFF4DA6`: **0** matching survey-source
  pages exist in the current 12-file fixture;
- capacity `ASSIGN-E9BD8EC7BDE545`: required
  `NOMINAL_TOTAL_CAPACITY` cannot be compared to observed
  `OPERATING_SECTION_THROUGHPUT`;
- equipment `ASSIGN-15C37B5DD8F8C8`: brand/manufacturer difference alone is
  insufficient for a categorical mismatch;
- object composition `ASSIGN-1AAA2D9BDB9338`: the current corpus does not
  safely prove the complete expected 38-object set;
- negative/applicability reviews: no candidate provides enough body-level subject
  agreement for categorical proof. The strongest title-level candidate
  `ASSIGN-9F6B4A19B43D82` has 2/3 title-term overlap but **0% body-term overlap**,
  so it correctly remains `REVIEW`;
- remaining generic presence/normative candidates are partial, owner-unresolved,
  qualifier-incomplete, or lack the required normative references.

### Development conclusion

Do **not** lower thresholds merely to force Test78 above 27/56.

For the current 12-document fixture, the next percentage gain should be accepted only
if new addressable evidence is discovered by a genuinely stronger reusable extractor or
if the benchmark corpus is expanded with the missing source documents.

Preferred architecture direction now:
1. keep 27/56 as the honest current benchmark;
2. extend source-to-project traceability beyond engineering surveys to other explicit
   source documents (e.g. technical conditions / source data) with the same anchor-based
   fail-closed contract;
3. later validate against a corpus containing real PD + II + IRD rather than weakening
   gates on the current reduced fixture.


## Validated traceability extension — technical conditions and explicit source data

Technical-conditions source commit:
`74838ebc3ec079037baeaa9c046751d13c7724b1`

Test-contract correction:
`fc9929b71e199ea99f1f9824a661ea47b2b690f0`

Explicit source-data / IRD source commit:
`54c9e57590ca05794018920d569acd34ca40c34b`

Green regression marker:
`5e6e2687d4a02194dddbbd90a18bc94e5ba2c8c4`

### Trace source roles

The same Core25 `TRACEABILITY` archetype now supports three explicit source roles:

- `SURVEY_REPORT` — engineering survey reports;
- `TECHNICAL_CONDITIONS` — technical conditions / TU;
- `SOURCE_DATA` — explicit owner/source data and IRD source documents.

No source role has its own verdict engine. All three feed the same fail-closed
two-sided proof contract.

### Universal proof contract

A source -> project trace can become categorical only when:

1. the Assignment requirement explicitly implies the corresponding source role;
2. the source page is addressable and classified as that source role;
3. the project page explicitly states adoption/use of that source role;
4. both pages share the same explicit report/reference anchor;
5. both pages share at least two non-generic engineering-subject terms;
6. source and project are different documents;
7. upstream qualification emits separate `SOURCE_INPUT` and `PROJECT_ADOPTION` roles;
8. Core25 re-validates the shared `trace_subject_key`, `trace_anchor`, and
   `trace_source_role`.

For `TECHNICAL_CONDITIONS` and `SOURCE_DATA`, trace qualification may override a
legacy `PRESENCE_REQUIREMENT` / `NORMATIVE_COMPLIANCE` / `SEMANTIC_ENGINEERING`
route only when the requirement explicitly names the source dependency.

### Regression guards

Synthetic end-to-end tests now cover:
- technical conditions -> project adoption with same anchor;
- technical conditions with mismatched anchor -> review;
- TU reference without source document -> review;
- explicit source data/IRD -> project adoption with same anchor;
- source data with mismatched anchor -> review;
- source-data reference without source document -> review.

A red CI at the TU commit was traced to an invalid test assertion:
`verification_kind` in the public row is intentionally overwritten with the final
public verdict. Production logic was not changed; the test now asserts the stable
proof state, reason code, and coverage executor.

### Current Test78 accounting

Both the TU extension and the SOURCE_DATA/IRD extension preserve the benchmark:

- `VERIFIED_OK`: **25**;
- `PROJECT_FINDING`: **2**;
- `REVIEW_QUESTION`: **29**;
- strict categorical coverage: **27/56 = 48.2%**;
- Test78 classification: **NO_CHANGE**;
- changed IDs: **none**.

This is expected: the current 12-document Test78 fixture does not contain the required
external source documents for these positive trace paths.

### Validation at `54c9e57...`

- Core25 Quality Leap gates: **success**;
- Core25 tests: **success**;
- baseline full diagnostic: **success**;
- Core20 regression: **success**;
- Core20 quality gates: **success**;
- results integrity: **success**;
- Validate ExpertCheck 25.2 branch: **success**;
- Source Snapshot Artifact: **success**;
- Test78 deterministic A/B: **success / NO_CHANGE**;
- alpha1 release gate: **success**.

### Continue from here

The 12-document frontier has now been audited deeply enough that forcing the next
percentage gain would require weakening gates.

Preferred next direction:
1. build or add a benchmark corpus that contains real PD + engineering surveys + IRD;
2. use it to measure the new cross-document trace archetype end-to-end;
3. keep Test78 at 27/56 until genuinely complete evidence appears in its fixture;
4. continue improving universal extractors only when they recover previously hidden,
   addressable evidence rather than infer missing documents.


## Validated benchmark — deterministic traceability contract suite

Benchmark commit:
`44204050841c3b362403b49a936bec195e2a1f23`

Workflow:
`.github/workflows/traceability-benchmark.yml`

Benchmark definition:
`knowledge/benchmarks/traceability_contract_v1.json`

Runner:
`tools/run_traceability_benchmark.py`

### Purpose

This benchmark is intentionally separate from Test78.

Test78 is a reduced 12-document fixture and currently lacks the external source
documents needed to exercise positive source-to-project traceability. The new benchmark
therefore measures the `TRACEABILITY` contract directly without changing the Test78
denominator or relaxing its gates.

It is a **synthetic contract benchmark**, not a substitute for a future real
PD + engineering-survey + IRD corpus.

### Current cases

Nine deterministic scenarios are included:

1. engineering-survey report -> project adoption, matching anchor -> `VERIFIED_OK`;
2. survey mismatched anchor -> `REVIEW_QUESTION`;
3. survey source missing -> `REVIEW_QUESTION`;
4. technical conditions -> project adoption, matching anchor -> `VERIFIED_OK`;
5. TU mismatched anchor -> `REVIEW_QUESTION`;
6. TU source missing -> `REVIEW_QUESTION`;
7. explicit source data / IRD -> project adoption, matching anchor -> `VERIFIED_OK`;
8. source-data mismatched anchor -> `REVIEW_QUESTION`;
9. source-data source missing -> `REVIEW_QUESTION`.

### Validated result

First workflow run:
- classification: **PASS**;
- cases: **9**;
- passed: **9**;
- failed: **0**.

The same commit also passed:
- Core25 tests;
- baseline full diagnostic;
- Core20 regression;
- Core20 quality gates;
- results integrity;
- Source Snapshot Artifact;
- alpha1 release gate.

No production logic changed in this benchmark commit.

### Test78 remains unchanged

The production source commit immediately before the benchmark was
`54c9e57590ca05794018920d569acd34ca40c34b`.

Its Test78 result:
- **NO_CHANGE**;
- `25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW`;
- strict coverage **27/56 = 48.2%**;
- `changed_ids=[]`.

### Continue from here

The next meaningful traceability milestone is a real external benchmark containing
PD + engineering surveys + IRD.

Until that corpus is available:
- keep the synthetic 9/9 contract suite as a regression guard;
- do not infer missing source documents from project references alone;
- do not raise Test78 by weakening source/anchor/subject gates.


## Validated checkpoint — adversarial traceability + upload source readiness

Adversarial benchmark commit:
`ef6bd05e2dcf541b84617ab85e6fcc2ef7c20cc9`

Upload source classification commits:
- `63776a1f4b2a4dab7f2c9b0d461e6e375c628a32` — source document types and package summary;
- `c0250094ba7c5fa8d22bfbd1ec2824e6ed962a69` — explicit source-role priority over thematic PD classification.

Upload UI commit:
`c1d77223a5318f85f0d1a05cce87a61505981dea`

### Adversarial traceability benchmark v1.1

The deterministic synthetic traceability suite was expanded from **9** to **14** cases.

New fail-closed negatives cover:
1. TU requirement with a SOURCE_DATA document carrying the same anchor;
2. SOURCE_DATA requirement with a TU document carrying the same anchor;
3. the same physical document used as both source and project evidence;
4. a generic numeric-only report anchor;
5. matching anchor but weak engineering-subject overlap.

Validated result:
- classification: **PASS**;
- cases: **14**;
- passed: **14**;
- failed: **0**.

No production logic was changed to make these cases pass; the existing source-role,
anchor, subject and independent-document gates already rejected them.

### Upload/source-document classification

The upload layer now recognizes explicit source document types:

- `ИГДИ / ИГИ / ИГМИ / ИЭИ` -> trace role `SURVEY_REPORT`;
- `ТУ` -> trace role `TECHNICAL_CONDITIONS`;
- `ИРД / Исходные данные` -> trace role `SOURCE_DATA`.

A first regression exposed a real filename-priority problem:
`ТУ_электроснабжение.pdf` was initially classified as `ИОС1` because the thematic
word `электроснабжение` matched before the source-document marker.

Accepted correction:
- explicit source-document roles are classified before thematic PD sections;
- thus a TU/IRD/source-data file cannot be silently converted into an IOS/PZ family
  merely because its filename names the engineering system it concerns.

### Package traceability preflight

`prepare_uploads()` now adds a compact `package_summary["traceability"]` block:

- `SURVEY_REPORT` count;
- `TECHNICAL_CONDITIONS` count;
- `SOURCE_DATA` count;
- available source roles;
- missing source roles;
- `traceability_ready` boolean.

The Project upload UI displays one compact line:

`ИИ — N · ТУ — N · ИРД/исходные данные — N`

If no source-side documents are recognized, the UI explicitly warns that
source-document -> PD traceability checks will be limited.

### End-to-end type propagation

The declared upload type is preserved through the analysis path:

1. `PreparedUpload.declared_document_type`;
2. legacy analyzer uses the declared type before its own classifier;
3. returned `documents["Тип документа"]`;
4. Core pipeline builds the `document_types` map;
5. `build_page_corpus()` writes that exact type into each page;
6. traceability qualification reads the page `document_type`.

Therefore the new TU/IRD/survey classifications reach the actual trace checker rather
than existing only in the upload screen.

### Current Test78 baseline

Production Test78 remains intentionally unchanged:
- `VERIFIED_OK`: **25**;
- `PROJECT_FINDING`: **2**;
- `REVIEW_QUESTION`: **29**;
- strict categorical coverage: **27/56 = 48.2%**;
- classification: **NO_CHANGE**;
- changed IDs: **none**.

### Validation

After the source-role priority fix:
- Core25 Quality Leap gates: **success**;
- Core25 tests: **success**;
- baseline full diagnostic: **success**;
- Core20 regression: **success**;
- Core20 quality gates: **success**;
- Validate ExpertCheck 25.2 branch: **success**;
- Source Snapshot Artifact: **success**;
- Test78 deterministic A/B: **success / NO_CHANGE**.

After the compact upload UI change:
- Core25 Quality Leap gates: **success**;
- Core20 quality gates: **success**;
- Source Snapshot Artifact: **success**.

### Continue from here

The traceability logic and upload classification are now aligned.

The next infrastructure risk for a real **800 MB–1+ GB** project package is memory
behaviour during ZIP preparation: the browser holds the uploaded ZIP while the current
upload preparation also materializes extracted PDF/XML members in memory.

Before claiming full-size package readiness, inspect and reduce this peak-memory path.
Do not solve it by lowering the 1.5 GB archive safety limit without changing storage
behaviour.


## Validated checkpoint — file-backed ZIP preparation

Source commit:
`278dd4129b131e6b065883924ccff681cc0907f2`

Green regression marker:
`6e43e4f74bbce9764c494e018f8b3be7749e88be`

### Problem addressed

The upload path previously retained:
1. the uploaded ZIP in Streamlit memory;
2. every extracted PDF/XML member as another in-memory byte array.

For large packages this creates a peak close to **ZIP bytes + full uncompressed corpus**
before engineering analysis even starts.

### Accepted behavior

Supported ZIP members are now extracted incrementally to a temporary directory:

- `archive.open(...)` streams each member;
- `shutil.copyfileobj(..., 1 MB chunks)` writes to disk;
- ZIP-derived `PreparedUpload` objects keep `backing_path/backing_size` instead of
  uncompressed `data` bytes;
- downstream code continues to use the same `getvalue()/read()` contract;
- direct non-ZIP uploads remain in memory;
- temporary resources are owned by `UploadPreparationResult` so staged files remain
  valid during the analysis lifecycle;
- duplicate hashing streams file-backed members in 1 MB chunks;
- package summary exposes file-backed/in-memory counts and bytes.

### Regression guards

Tests verify:
- ZIP member is file-backed and readable through the existing contract;
- direct upload remains in-memory;
- source-document classification and traceability summaries remain intact.

### Validation

At `278dd412...`:
- Core25 Quality Leap gates: **success**;
- Core25 tests: **success**;
- baseline full diagnostic: **success**;
- Core20 regression: **success**;
- Core20 quality gates: **success**;
- results integrity: **success**;
- Validate ExpertCheck 25.2 branch: **success**;
- Source Snapshot Artifact: **success**;
- Test78 deterministic A/B: **success / NO_CHANGE**;
- Test78 remains **25 VERIFIED + 2 PROJECT_FINDING + 29 REVIEW = 27/56**;
- changed IDs: **none**.

### Remaining large-package limitation

This does **not** yet make 800 MB–1+ GB browser uploads production-ready.

Current Streamlit configuration still has:
- `server.maxUploadSize = 500`;
- `server.maxMessageSize = 500`.

Even after file-backed extraction, Streamlit still owns the original uploaded ZIP buffer.
Do not simply raise these limits and claim large-package readiness.

Preferred next step:
- stage the prepared file-backed package across a Streamlit rerun;
- release/reset the original uploader before expensive analysis;
- then measure the remaining upload-buffer lifetime and peak-memory path.


## Validated checkpoint — uploader staging before analysis

Source commit:
`9e7a15370afb7ddc1bd193fadde9dbc8358e9d1c`

### Accepted lifecycle

The Project page now separates upload/preparation from heavy analysis across a
Streamlit rerun:

1. browser uploads one ZIP or a direct PDF/XML batch;
2. `prepare_uploads()` prepares the package;
3. the resulting `UploadPreparationResult` is stored only in transient
   `st.session_state`;
4. the active uploader widget key is rotated and explicitly removed on the next run;
5. the next run renders the staged package without recreating the uploader;
6. analysis uses only staged `PreparedUpload` objects;
7. after successful analysis, staged package/editor/confirmation state is cleared and
   temporary files can be released;
8. after an analysis failure, the staged package remains available for retry.

This is intentionally transient: staged source files are not added to the persisted
workspace snapshot/database.

### Why this matters

Together with file-backed ZIP members, expensive analysis no longer needs to retain the
browser ZIP widget plus the full unpacked project corpus at the same time.

This still does not bypass Streamlit's configured per-upload limit of 500 MB.

### Validation

The first release-gate attempt failed **before tests** because PyPI repeatedly timed out
while resolving `python-dateutil`. The failed release jobs were rerun without changing
the source code.

On rerun:
- dependency installation: **success**;
- focused regressions: **success**;
- legacy full-suite against allowlist: **success**;
- Compile Core25: **success**;
- Core25 tests: **success**;
- baseline full diagnostic: **success**;
- Core20 regression: **success**;
- Core20 quality gates / integrity: **success**;
- Source Snapshot Artifact: **success**.

No Test78 semantics were changed by this UI/lifecycle work.

### Next step

Do not raise `.streamlit/config.toml` to a 1+ GB single-file upload yet.

Prefer sequential multipart staging:
- each ZIP part stays below the existing 500 MB per-upload limit;
- extract one part to file-backed staging;
- release its uploader buffer;
- add the next ZIP part;
- merge staged inventories;
- run one analysis on the combined file-backed project package.

This can support an aggregate project larger than the single-upload limit without
holding the whole archive set in browser memory at once.


## Validated checkpoint — sequential multipart ZIP staging

Final source commit:
`ecca1a15c8e35efa17cbc339de30c6c9b1a44fac`

Green regression marker:
`93b41afeeecd5215cb8efd093e970ffe632a2b7f`

Supporting commits:
- `63c28222b58d2fe47ae6e3f36df72ba7c9471fa0` — merge staged package parts without rematerialising bytes;
- `8e3b8f8208aa964928165dffe79d078049500a9f` — sequential ZIP-part UI;
- `a0ff895f7f19706c47b3d509a7b7af210bf5a86b` — aggregate safety tests/UI handling;
- `ecca1a15c8e35efa17cbc339de30c6c9b1a44fac` — enforce aggregate limits inside the merge path itself.

### Purpose

The configured Streamlit single-file upload limit remains **500 MB**.
Rather than raising it to 1+ GB and keeping a giant browser buffer alive, ExpertCheck can
now assemble one project package from sequential ZIP parts.

### Accepted multipart lifecycle

1. Upload one ZIP part under the existing per-file transport limit.
2. Prepare/extract it to file-backed staging.
3. Rotate/remove the uploader widget on rerun.
4. Keep only the staged package and its temporary-file owners.
5. Select **Добавить ZIP-часть**.
6. Upload the next ZIP part.
7. Prepare it independently and merge metadata/file references into the staged package.
8. Deduplicate exact cross-part duplicates.
9. Rerun again to release that uploader buffer.
10. Repeat as needed, then review the combined inventory and run one analysis.

The editable inventory and **Запустить проверку** are hidden while a new ZIP part is
being added, so an incomplete assembly cannot be launched accidentally.

### Memory property

Merging packages does not copy staged PDF/XML bytes back into RAM.

The merged result retains the `TemporaryDirectory` owners from every staged part, so
file-backed members remain readable after intermediate package objects leave scope.

### Aggregate safety

Multipart cannot bypass the original archive safety envelope.

The merged package is rejected when:
- supported files exceed `MAX_ARCHIVE_ENTRIES = 2500`; or
- total staged uncompressed PDF/XML bytes exceed
  `MAX_UNCOMPRESSED_BYTES = 1.5 GiB`.

These limits are checked on the **combined** staged package after deduplication.

Unit tests cover:
- two staged ZIP parts remain file-backed after merge;
- temporary backing paths stay alive through the merged result;
- exact duplicate members across parts are removed;
- aggregate byte limit is enforced;
- aggregate file-count limit is enforced.

### CI note

Several first-attempt diagnostic/integrity jobs during this work failed before tests
because PyPI repeatedly timed out fetching `python-dateutil`.
Those failed jobs were rerun without source changes and then passed.

### Validation

At final source `ecca1a1...`:
- Core25 tests: **success**;
- Core20 regression: **success**;
- baseline full diagnostic: **success after network retry**;
- alpha1 release gate: **success**;
- Core20 quality / results integrity: **success**;
- Validate ExpertCheck 25.2: **success**;
- Source Snapshot Artifact: **success**;
- Test78 deterministic A/B: **success / NO_CHANGE**;
- Test78 remains **25 VERIFIED + 2 PROJECT_FINDING + 29 REVIEW = 27/56**;
- changed IDs: **none**.

### Current readiness statement

Architecture now supports assembling a project larger than the 500 MB single-upload
limit through sequential ZIP parts while keeping staged members file-backed.

This is **ready for manual browser validation**, not yet a claim that a real 800 MB–1 GB
package has been proven in production. A real multipart upload should be tested before
calling the large-package milestone complete.


## Validated checkpoint — report Quality Gate respects Core25 authoritative proof

Source commit:
`3fe4b8a1e54d81c2f9ef2556c1cd6a8c77e087fc`

Green validation marker:
`7e80cf71970a191bc83c23a4cf207cba7cbbd4c2`

### Problem reproduced in Streamlit

A manual 12-file project run without a full AI pass produced categorical Core25
assignment results whose canonical Verified Core gate had already passed, but the
report Quality Gate still emitted repeated errors equivalent to:

`Категоричный вывод не имеет пройденной проверки достаточности`.

The conflict came from two different contracts:
- Core25 categorical results may be authoritative through their canonical public
  Routing → Evidence → Binding → Proof → Decision trace;
- the legacy report Quality Gate independently required
  `adversarial_state == PASSED` for every categorical result.

That second requirement incorrectly treated a deterministic Core25 L5 proof as if it
still required the legacy adversarial/AI route.

### Fix

`core/report_quality_gate.py` now recognizes
`verified_core_gate.core25_authoritative == True`.

For that narrowly defined route:
- `verified_core_gate_state == PASSED` remains mandatory;
- addressable evidence remains mandatory;
- an explicit `adversarial_state == BLOCKED` is still rejected by the existing
  contradiction checks;
- absence of a legacy adversarial pass is no longer reported as a Quality Gate error.

All non-Core25 categorical routes retain the previous adversarial requirement.

Regression tests were added for both sides of the contract:
- authoritative deterministic Core25 verdict without legacy adversarial pass is accepted;
- non-Core25 categorical verdict without adversarial pass is still rejected.

### Validation

At source `3fe4b8a1...`:
- Core20 quality gates: **success**;
- Core25 tests: **success**;
- Core20 regression: **success**;
- baseline full diagnostic: **success**;
- Validate ExpertCheck 25.2: **success**;
- full legacy repository suite against allowlist: **success**;
- alpha1 release gate: **success**;
- Test78 deterministic A/B: **success / NO_CHANGE**;
- Test78 remains **25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56**;
- changed requirement IDs: **none**.

### Next step

Repeat the short Streamlit run on the same 12-file package without a full AI pass and
re-export the three reports. The expected result is that deterministic Core25
categorical rows no longer create false report Quality Gate errors solely because the
legacy adversarial/AI route was not executed.


## Validated checkpoint — manual Streamlit report Quality Gate regression

Validated code lineage:
- report Quality Gate fix: `3fe4b8a1e54d81c2f9ef2556c1cd6a8c77e087fc`
- preserve Core25 gate in review plan: `06c85aa48dbae415876a656c788eae6820d9d69a`
- integration test: `afbc54332533490734145718e83e3841ec21b070`
- CI trigger/current validated source: `4d188d63d73ac7063b17e6047fecbe54ac9a94da`
- green regression marker: `a990bc7110529809e25c119ff87164871ab5fee2`

### Manual Streamlit evidence

The saved 12-document DSK project was reopened in Streamlit on the current 25.2 branch.
No full project re-upload was required and no additional full AI run was used for this
validation. Reports were regenerated from the saved analysis state.

Before the propagation fix, each exported report contained 28 false Quality Gate errors
(QG-001 through QG-028) stating that categorical results lacked a completed sufficiency
check even though their Core25 canonical Verified Core proof had already passed.

After preserving the full `verified_core_gate` contract into `build_review_plan`:
- Executive Summary report: **0 QG false-error matches**;
- GIP report: **0 QG false-error matches**;
- Technical Appendix: **0 QG false-error matches**;
- the Report Control sheet collapsed from 32 rows to 4 rows;
- report integrity/control status is **PASSED / Пройден**;
- report status changed from
  **Предварительный — Quality Gate отчёта не пройден**
  to **Итоговый — проверка неполная**.

This is not a claim that the project review is complete. The report correctly remains
incomplete because specialist questions, automation gaps, project completeness and the
remaining AI queue still exist.

### Result preservation

The correction did not hide real project findings. The regenerated reports still show:
- 3 confirmed project findings;
- 62 specialist review questions;
- 673 checks outside current automatic coverage.

The three confirmed findings remain:
1. compressor building footprint conflict: PZ 54.3 m² vs PZU 48.7 m²;
2. identification-attribute mismatch for the assignment requirement;
3. SHANTUI L76-C5 assignment vs ARKTOS L76-C5 / quantity mismatch.

### CI / deterministic safety

At source `4d188d63...`:
- Core20 quality gates: **success**;
- Core25 tests: **success**;
- Core20 regression: **success**;
- baseline full diagnostic: **success**;
- Validate ExpertCheck 25.2: **success**;
- alpha1 release gate / full legacy suite: **success**;
- Test78 deterministic A/B: **success / NO_CHANGE**;
- Test78 remains **25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56**;
- changed requirement IDs: **none**.

### Next step

Quality Gate/report propagation defect is closed.

Return to product-quality work rather than report plumbing. Use the manual Streamlit
results to choose the next high-value weakness: evidence quality / false review noise,
NTD proof coverage, checklist coverage, or a specific Test78 REVIEW frontier candidate.


## Validated checkpoint — normative knowledge wave 1

Validated lineage:
- `88c7125a50dd377dfe636bb89bd3f2c920073cc1` — add verified 384-FZ and GOST 27751 knowledge package;
- `8b9b39776b7e21c9f1f20a37f2b5cb81347682f3` — upgrade existing GOST 27751 validity record instead of shadowing it;
- `cf490fe41ca24c1f79b4b5398043307daa131fdd` — run Test78 automatically on normative knowledge-file changes.

### Scope

Knowledge-only expansion; Core verdict logic was not changed.

Catalogue:
- normative documents: 8 -> 9;
- atomic requirements: 61 -> 68;
- newly curated verified clauses: 7.

New verified clauses:
- 384-FZ art. 4 part 1 — identification features;
- 384-FZ art. 4 part 7 — responsibility level;
- 384-FZ art. 4 part 11 — identification features in design assignment and PD;
- 384-FZ art. 15 part 2 — responsibility level in design input data;
- 384-FZ art. 15 part 5.1 — justification of compliance with safety requirements;
- GOST 27751-2014 cl. 10.1 / table 2 — class, responsibility level and reliability coefficient consistency;
- GOST 27751-2014 cl. 10.2 — assignment of class, level and coefficient in the design assignment.

Full normative texts were not copied into the repository. The package stores source metadata,
clause addresses, paraphrased atomic requirements and proof contracts.

### Source verification

384-FZ:
- current consolidated revision: 25.12.2023, effective from 01.09.2024;
- amendment basis: Federal Law No. 653-FZ, official publication
  `0001202312250053`.

GOST 27751-2014:
- Rosstandart status: active;
- Amendment No. 1 effective 01.02.2023;
- correction published in IUS 4-2026 and effective 20.04.2026.

The historical validity corpus already contained GOST 27751-2014 as an unverified citation.
That existing canonical record was upgraded in place, preserving its historical expert
statistics (48 occurrences / 16 projects), rather than adding a duplicate canonical_id.

### Regression control

Test78 workflow now listens to:
- `knowledge/normative_documents_registry.json`;
- `knowledge/normative_validity_registry.json`;
- `knowledge/normative_requirements_v3.json`.

At `cf490fe4...`:
- Core20 quality gates: success;
- Core25 tests: success;
- Core20 regression: success;
- baseline full diagnostic: success;
- alpha1 release gate / legacy full suite: success;
- Test78: success / NO_CHANGE;
- 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

### Next validation

Open the saved 12-document DSK project on the current branch without re-uploading the PDFs.
Rebuild/reopen the normative route and reports, then compare:
- known documents;
- verified clauses;
- executable contracts;
- routed verified clauses;
- normative evidence coverage;
- semantic queue;
- specialist review count.

Do not add wave 2 until the real-project effect of wave 1 is measured.


## Validated checkpoint — normative knowledge wave 2: fire safety

Source commit:
`4922d8958e291431683cf6a455fbba6d3426fb0b`

### Scope

Knowledge-only expansion. Core verdict logic was not changed.

Catalogue after wave 2:
- normative documents: 11;
- atomic requirements: 79;
- newly added verified clauses in this wave: 11.

Documents curated in wave 2:
- Federal Law No. 123-FZ, current revision 04.08.2026;
- SP 4.13130.2013, active with Amendments No. 1–4;
- SP 12.13130.2009, active with Amendment No. 1.

Verified atomic clauses added:
- 123-FZ art. 27 part 3 — inputs for fire/explosion categorisation;
- 123-FZ art. 27 part 22 — categories must be stated in project documentation;
- 123-FZ art. 78 part 1 — fire-technical characteristics in project documentation;
- 123-FZ art. 92 part 2 — standalone fire-safety systems section for production objects;
- SP 12.13130.2009 cl. 4.1 — category taxonomy for rooms/buildings/outdoor installations;
- SP 12.13130.2009 cl. 4.2 — categorisation input factors;
- SP 12.13130.2009 cl. 5.2 — sequential category determination A → D;
- SP 4.13130.2013 cl. 6.1.2 / table 3 — fire separation distances for production sites;
- SP 4.13130.2013 cl. 8.2.1 — number of fire-access sides;
- SP 4.13130.2013 cl. 8.2.3 — minimum fire-road width by building height;
- SP 4.13130.2013 cl. 8.2.6 — road-edge-to-wall distance by building height.

Full normative texts were not copied into the repository. Only source metadata,
clause addresses, paraphrased atomic requirements and proof contracts were stored.

### Source status

123-FZ:
- current revision verified as 04.08.2026;
- latest amendment in the consolidated revision: Federal Law No. 330-FZ of 04.08.2026.

SP 4.13130.2013:
- Rosstandart status: active;
- Amendment No. 4 effective from 01.12.2023.

SP 12.13130.2009:
- Rosstandart status: active;
- Amendment No. 1 effective from 01.02.2011.

Existing historical validity records for 123-FZ and SP 4 were upgraded in place,
preserving expert-history statistics. SP 12 was added as a new canonical validity record.

### Regression control

At `4922d895...`:
- Core20 tests: success;
- results-integrity: success;
- Core25 tests: success;
- Core20 regression: success;
- baseline full diagnostic: success;
- alpha1 release gate / legacy full suite: success;
- Test78: success / NO_CHANGE;
- Test78 remains 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

### Next validation

Open the saved 12-document DSK project on the current branch. No PDF re-upload and no
full AI project run are required.

On "НТД и практика", compare wave-1 baseline:
- executable contracts: 39;
- candidate evidence: 63;
- proved: 11 after partial semantic proof;
- specialist questions: 26;
- system limitations: 2;
- addressable evidence: 69.2%.

Measure how wave 2 changes contract count, candidate evidence, addressable evidence,
semantic queue and deterministic proof before starting another semantic-AI batch.


## Validated checkpoint — wave 2 DSK measurement and semantic-proof persistence

Current validated lineage:
- wave 2 fire-safety knowledge: `4922d8958e291431683cf6a455fbba6d3426fb0b`;
- wave 2 checkpoint: `4c7b737c078b0f14462cb5d430ed47be41f31479`;
- per-packet semantic reuse implementation: `540101f62126024cb6e6ed69e2ddf060e4da2b47`;
- source-packet fingerprint correction: `e71668803045d373d5f0258e1d365dba96f6b669`;
- Test78 Core20 trigger: `cc56eee00a006ba584ed0aaab8b50d481ac82df0`.

### Manual Streamlit measurement after wave 2

Saved 12-document DSK project, no re-upload and no new semantic-AI run:

Knowledge:
- documents: 11;
- validity records: 152;
- atomic requirements: 79;
- verified clauses: 50;
- projects linked with NTD history: 20.

Project routing:
- project-relevant routes: 79;
- verified-clause routes: 50;
- executable contracts: 50;
- history-prioritized routes: 61.

Normative execution:
- contracts: 50;
- evidence candidates: 87;
- deterministic proved: 7;
- demoted/held by proof control: 21;
- semantic queue: 18;
- semantic proof applied: 0;
- specialist questions: 41;
- system limitations: 2;
- addressable evidence coverage: 68.0%.

Wave-1 deterministic baseline before its AI semantic pass was:
39 contracts / 63 candidates / 7 proved / 18 held / 15 semantic queue /
0 semantic applied / 30 specialist questions / 2 limitations / 69.2% addressable.

Therefore wave 2 itself added:
- +11 executable contracts;
- +24 evidence candidates;
- +3 proof-controlled holds;
- +3 semantic-queue items;
- +11 specialist-review rows;
while preserving deterministic proved count and nearly preserving addressable-evidence ratio.

### Semantic proof persistence defect and fix

The previous wave-1 partial semantic run had produced 4 independent semantic confirmations
(7 -> 11 proved; 30 -> 26 specialist questions). After wave 2 enlarged the normative queue,
those confirmations were not reused because semantic proof was gated by one fingerprint of
the entire queue.

The corrected contract is fail-closed and per-packet:
- each newly generated semantic decision stores a fingerprint of the original normative
  packet (requirement + proof type + addressable evidence);
- when the knowledge base expands, a prior decision is reused only if that individual
  packet fingerprint is unchanged;
- changed requirement text, proof type, evidence address, or evidence fragment invalidates
  reuse for that packet;
- legacy semantic decisions created before this change do not contain per-packet
  fingerprints and are therefore not silently trusted after a queue change.

This means the 4 old wave-1 semantic confirmations require one safe revalidation under the
new format; future knowledge waves will preserve unchanged confirmations.

### Validation

At the semantic-persistence source:
- Core20 tests: success;
- results-integrity: success;
- Core25 tests: success;
- Core20 regression: success;
- baseline full diagnostic: success;
- alpha1 release gate / full legacy suite: success.

Test78 is now triggered by `core20/**` as well as `core/**`, `core25/**` and normative
knowledge files.

At `cc56eee0...`:
- Test78: success / NO_CHANGE;
- 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

### Next step

Do not add wave 3 yet. Reopen the saved DSK project on the current branch and perform one
bounded normative semantic run when providers are available. This will create the new
per-packet checkpoint format. Then record the post-AI wave-2 metrics and only after that
start the next knowledge wave.


## Validated checkpoint — normative knowledge wave 3: mining, lighting, site planning

Source commit:
`ba6bb233ffc35adf5f714fed0f70975ecbb4f649`

### Scope

Knowledge-only expansion. Core verdict logic was not changed.

Catalogue after wave 3:
- normative documents: 13;
- atomic requirements: 86;
- newly added verified clauses in this wave: 7.

Documents curated in wave 3:
- FNP mining/mineral-processing rules, Order of Rostechnadzor No. 505 of 08.12.2020,
  current revision 24.03.2026, term extended to 01.09.2032;
- SP 52.13330.2016, active with Amendments No. 1–2;
- SP 18.13330.2019, active with Amendments No. 1–5; Amendment No. 5 effective 04.09.2026.

Verified atomic clauses added:
- FNP 505 cl. 1184 — fire-safety package for belt conveyors in galleries;
- FNP 505 cl. 1215 — bridge crossing spacing over conveyors;
- FNP 505 cl. 1461 — emergency lighting on surface-complex workplaces;
- SP 52.13330.2016 cl. 7.6.1 — emergency-lighting power-loss behavior;
- SP 52.13330.2016 cl. 7.6.3 — evacuation-route lighting;
- SP 18.13330.2019 cl. 5.37 — production-site entrance gate width;
- SP 18.13330.2019 cl. 5.52 — closed storm-water sewer on production-site territory.

Full normative texts were not copied into the repository. Only source metadata,
clause addresses, paraphrased atomic requirements and proof contracts were stored.

### Source status

FNP 505:
- current consolidated revision: 24.03.2026;
- Order No. 94 effective 10.05.2026 extended the validity term to 01.09.2032;
- official publication identifier for the amendment: 0001202604290007.

SP 52.13330.2016:
- Rosstandart status: active;
- Amendments No. 1 and No. 2 are published by Rosstandart;
- cl. 7.6.3 is also included in the current mandatory-requirements list effective from 01.06.2026.

SP 18.13330.2019:
- Rosstandart status: active;
- Amendments No. 1–5;
- Amendment No. 5 registered 26.08.2026 and effective 04.09.2026.

Existing historical validity records for SP 52 and SP 18 were upgraded in place,
preserving expert-history statistics. The generic FNP-MINING catalog record was upgraded
to the concrete Order No. 505 contract and linked to a new canonical validity record.

### Regression control

At `ba6bb233...`:
- Core20 tests: success;
- results-integrity: success;
- Core25 tests: success;
- Core20 regression: success;
- baseline full diagnostic: success;
- alpha1 release gate / full legacy suite: success;
- Test78: success / NO_CHANGE;
- Test78 remains 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

### Manual baseline before wave 3

Wave-2 post-semantic-run DSK state:
- executable contracts: 50;
- candidate evidence: 87;
- proved: 11;
- semantic proof applied: 4;
- semantic queue: 14;
- specialist questions: 37;
- system limitations: 2;
- addressable evidence: 68.0%.

### Next validation

Open the same saved 12-document DSK project on the current branch with no PDF re-upload
and no new AI run.

First verify semantic-proof persistence:
- the existing 4 semantic confirmations should remain applied after the wave-3 knowledge
  expansion if their per-packet fingerprints are unchanged.

Then capture the new wave-3 project metrics:
- verified-clause routes;
- executable contracts;
- candidate evidence;
- proved;
- semantic proof applied;
- semantic queue;
- specialist questions;
- addressable evidence.

Do not start another semantic-AI batch until this no-AI persistence check is observed.


## Validated checkpoint — wave 3 normative retrieval/applicability fix

Validated lineage:
- wave 3 knowledge checkpoint: `d32c50415d85fd90ff19a0d8752e9fbd0a1eaeee`;
- retrieval/applicability source: `3ee1cec3a04bb0e1b689d7a872ae04307e62548c`;
- test-fixture correction only: `48491071aa2226fec872b86b919c9a586ce76e31`.

### Manual diagnosis from the 12-document DSK corpus

Wave 3 added seven executable requirements but only three additional evidence candidates.
The reason was upstream of AI:

1. conditional applicability was hard-coded for only one special case
   (`объект производственного назначения`), so curated conditional clauses for conveyor
   crossings and entrance gates could be stopped before evidence retrieval;
2. evidence retrieval matched full keyword phrases as exact substrings and counted bare
   dimensions such as `50 м` / `100 м` as independent keyword hits.

The real DSK corpus contains examples that expose both weaknesses:
- KR states that transition bridges over conveyors are arranged at intervals not greater
  than 100 m, but wording differs morphologically from the curated keyword phrase;
- PZU states that vehicle-entry gates are 4.5 m wide using the word order
  `ворота ... шириной 4,5 м`;
- IOS contains explicit emergency/evacuation-lighting descriptions.

### Fix

`core20/normative_execution.py` now:
- supports structured, corpus-proven conditional applicability through
  `evidence_contract.applicability_keywords` and `applicability_min_hits`;
- performs morphology-tolerant, order-independent local phrase matching using conservative
  token stems inside a bounded evidence window;
- keeps exact phrase matching when available;
- treats pure numeric thresholds as supporting evidence only — a page with numbers but no
  textual concept cannot become a normative candidate;
- preserves all existing proof gates: retrieval still does not create a categorical
  semantic/typed conclusion.

Structured applicability was added only where it can be proven from explicit project
content without making a legal inference:
- FNP 505 cl. 1215 — conveyor presence;
- SP 18.13330.2019 cl. 5.37 — gates + vehicle-entry context;
- FNP 505 cl. 1184 — only an explicit conveyor-gallery concept can establish applicability.

FNP 505 cl. 1461 remains fail-closed because applicability to the surface-complex workplace
set is not yet encoded with a sufficiently reliable project predicate.

### Regression tests

Added coverage proves that:
- a real conveyor-crossing fragment outranks an unrelated page containing only 50 m / 100 m;
- `ширина ворот` matches `ворота ... шириной 4,5 м` without exact word order/case;
- a purely numeric page does not become normative evidence.

The first test fixture accidentally contained the word `конвейерах` in a sentence saying
that conveyor information was absent, which correctly triggered the applicability anchor.
That fixture alone was corrected in `48491071...`; production code was unchanged.

### Validation

For production code `3ee1cec3...`:
- Test78: success / NO_CHANGE;
- 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

At current HEAD `48491071...`:
- Core20 tests: success;
- results-integrity: success;
- Core20 regression: success;
- Core25 tests: success;
- baseline full diagnostic: success;
- alpha1 release gate / full legacy suite: success.

### Next Streamlit check

Use the same saved 12-document DSK project. Do not re-upload PDFs and do not run AI.

Wave-3 pre-fix baseline:
- executable contracts: 57;
- evidence candidates: 90;
- proved: 11;
- semantic proof applied: 4;
- semantic queue: 14;
- specialist questions: 44;
- system limitations: 2;
- addressable evidence: 63.2%.

Expected qualitative result after this fix:
- the 4 existing semantic confirmations remain preserved;
- candidate evidence and/or addressable evidence increase for wave-3 clauses;
- FNP 505 cl. 1215 and SP 18 cl. 5.37 should route to addressable semantic evidence rather
  than stopping at generic conditional applicability;
- no new categorical normative conclusion should appear without the existing proof gates.


## Validated checkpoint — selected-evidence semantic-proof persistence

Validated lineage:
- retrieval/applicability fix: `3ee1cec3a04bb0e1b689d7a872ae04307e62548c`;
- retrieval test-fixture correction: `48491071aa2226fec872b86b919c9a586ce76e31`;
- selected-evidence semantic persistence: `2c4da63dbc33f597ae2c47c0b7ee2823d421d333`;
- legacy fail-closed test correction: `609f7f11e290315b9a935976f5d48325b683d5cf`.

### Manual Streamlit signal after retrieval improvement

Same saved 12-document DSK project, no new AI run:

Before retrieval improvement:
- contracts: 57;
- evidence candidates: 90;
- proved: 11;
- semantic proof applied: 4;
- semantic queue: 14;
- specialist questions: 44;
- system limitations: 2;
- addressable evidence: 63.2%.

After retrieval improvement:
- contracts: 57;
- evidence candidates: 120;
- proved: 9;
- semantic proof applied: 1;
- semantic queue: 27;
- specialist questions: 45;
- system limitations: 3;
- addressable evidence: 73.7%.

Interpretation:
- retrieval materially improved (+30 candidates, +10.5 pp addressable evidence);
- three prior semantic confirmations became stale because the per-packet fingerprint included
  the entire top-candidate pool, so re-ranking/adding alternatives changed the packet even
  when the Judge-selected proof evidence could remain valid.

### Persistence fix

New semantic decisions now store:
- requirement fingerprint;
- selected-proof fingerprint;
- selected addressable evidence.

On later queue/candidate changes, a decision is reused only if:
1. the requirement + proof type are unchanged;
2. every evidence fragment actually selected by Judge is still present at the same
   document/page and contains the same judged fragment;
3. the selected-proof fingerprint matches.

Adding or re-ranking alternative candidates no longer invalidates a proven semantic result.
Changing the selected evidence or the requirement still invalidates it fail-closed.

Legacy decisions created before this selected-proof format are not silently upgraded after a
packet mismatch; they require one safe revalidation.

### Regression coverage

Tests now verify:
- candidate-pool growth preserves a proof whose selected evidence is unchanged;
- changed selected evidence invalidates proof;
- changed requirement invalidates proof;
- a legacy stale decision without selected-proof fingerprint remains fail-closed.

### Validation

At production source `2c4da63d...`:
- Test78: success / NO_CHANGE;
- 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

At current HEAD `609f7f11...`:
- Core20 tests: success;
- results-integrity: success;
- Core20 regression: success;
- Core25 tests: success;
- baseline full diagnostic: success;
- alpha1 release gate / full legacy suite: success.

### Next step

Do not add wave 4 yet.

Open the same saved DSK project on the current branch without re-uploading PDFs and without
running AI. Current legacy semantic checkpoint may still retain only the one decision whose
old packet fingerprint already matched, because the other three old decisions do not have
the new selected-proof fingerprint.

Run one bounded normative semantic batch only after confirming the no-AI state. That run will
write the new selected-proof format. Subsequent retrieval or knowledge expansion should then
preserve unchanged semantic confirmations.


## Validated checkpoint — cross-document evidence diversity

Validated lineage:
- selected-evidence semantic persistence checkpoint: `4576af63380e30dcda912f31852082449f18b14c`;
- source-diversity implementation: `f1950f9ba878eb03d49cc6422fd2b9438e5ca6ed`;
- evidence-quality overlay integration: `caeccb3b43046230f2012c74cf016c005784bb12`;
- isolated diversity test: `c77728b63cfd37c20f12e447055c4bb5ee873875`;
- current validated CI source: `1bbaa60039f5a6c984691025a12c9a6ffff3329d`.

### Problem

Cross-document normative requirements such as 384-FZ art. 4 part 11 can have many
high-scoring pages from one section (for example repeated identification tables in KR).
The previous top-4 retrieval could therefore use all four slots from one section and omit
the Design Assignment or PZ even when those sources contained the legally relevant
cross-document evidence.

### Fix

For contracts with `check_kind == CROSS_DOCUMENT` and `minimum_sources >= 2`:
- the strongest existing candidates are preserved;
- only the remaining evidence slots are used to increase section/source diversity;
- ordinary single-document contracts keep their previous ordering.

The diversity step is implemented as a shared Core20 helper and is also applied inside the
mandatory Alpha 10.1.2 evidence-quality overlay. Therefore source diversity does not bypass:
- table-of-contents rejection;
- topic-alignment gating;
- substantive-page quality checks.

For the common two-source / four-candidate case, the strongest first three candidates are
preserved and the fourth slot may be replaced by the best candidate from another section.

### Persistence relevance

This change is intentionally suitable for the selected-evidence persistence check:
it can add/reorder an alternative cross-document candidate while preserving the strongest
existing evidence. A previously confirmed semantic proof should remain reusable if the
Judge-selected document/page/fragment is still present and unchanged.

### Validation

At current source `1bbaa600...`:
- Core20 tests: success;
- results-integrity: success;
- Core20 regression: success;
- Core25 tests: success;
- baseline full diagnostic: success;
- alpha1 release gate / full legacy suite: success;
- Test78: success / NO_CHANGE;
- Test78 remains 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

### Next Streamlit check

Use the same saved 12-document DSK project.

Do not re-upload PDFs and do not run AI.

Pre-change baseline:
- contracts: 57;
- evidence candidates: 120;
- proved: 11;
- semantic proof applied: 3;
- semantic queue: 23;
- specialist questions: 43;
- system limitations: 3;
- addressable evidence: 73.7%.

Primary success criterion:
- `semantic proof applied` remains **3** after project rebuild/reboot.

Secondary signals:
- evidence candidates may stay 120 or change slightly because the top-4 composition changes;
- cross-document rows should include evidence from more than one section when eligible;
- no new categorical result is allowed solely because of source diversity.


## Validated checkpoint — Alpha 10 resumable queue aligned with selected-evidence reuse

Validated source:
`2bf4e9ab7b7ed46162bdca1b428340cd686e9e88`

### Root cause of 23 -> 27 semantic queue after reboot

The observed increase from 23 pending semantic packets in the live post-AI session to 27
after reboot was not caused by four new normative requirements from source diversity.

Only two current verified clauses are eligible for the new CROSS_DOCUMENT source-diversity
contract:
- FZ384-4-11-ID-IN-ASSIGNMENT-PD;
- GOST27751-10.2-ASSIGNMENT.

The actual cause was the Alpha 10.1 resumable-queue overlay.

The base semantic-proof layer already supported per-decision reuse across candidate-pool
changes through the selected-evidence fingerprint. This was visible in Streamlit because
three semantic confirmations survived retrieval changes and reboot.

However, Alpha 10.1 independently treated a semantic decision as processed only when the
fingerprint of the complete root queue exactly matched. When retrieval changed the candidate
pool, the base layer correctly reused the three unchanged selected-evidence decisions, but
Alpha 10.1 still counted those packets as pending. Therefore:
- semantic proof applied remained 3;
- pending semantic queue incorrectly returned from 23 to 27.

### Fix

Alpha 10.1 no longer duplicates the coarse whole-queue compatibility gate.

It now:
1. filters the persisted checkpoint to real completed Judge/Critic decisions;
2. delegates compatibility/reuse to the base semantic-proof layer;
3. reads which decisions were actually attached back to current proof rows;
4. treats exactly those reusable completed decisions as processed;
5. exposes as pending only current semantic packets without a safely reusable completed
   decision.

Consequences:
- candidate-pool growth/re-ranking does not re-add an unchanged judged packet to pending;
- changed selected evidence still returns the packet to pending;
- changed requirement/proof contract remains fail-closed;
- provider placeholders and incomplete SUPPORTS-without-Critic decisions remain pending.

### Regression coverage

Added Alpha 10 tests verify:
- a changed root queue with additional alternative evidence preserves a completed decision
  when the selected evidence is unchanged and removes that packet from pending;
- changing the selected evidence makes the packet pending again.

Existing tests continue to verify:
- exact-root resumable queue behavior;
- multiple semantic runs merge on the same root;
- checkpoints from another project/root are rejected;
- provider failures do not consume a packet;
- SUPPORTS without Critic remains pending.

### Validation

At `2bf4e9ab...`:
- Core20 tests: success;
- results-integrity: success;
- Core20 regression: success;
- Core25 tests: success;
- baseline full diagnostic: success;
- alpha1 release gate / full legacy suite: success;
- Test78: success / NO_CHANGE;
- 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

### Next Streamlit check

Use the same saved DSK project.

Do not upload PDFs and do not run AI.

Pre-fix live checkpoint:
- contracts: 57;
- candidate evidence: 120;
- proved: 11;
- semantic proof applied: 3;
- pending semantic queue after reboot: 27 (incorrect);
- specialist questions: 43;
- system limitations: 3;
- addressable evidence: 73.7%.

Primary success criterion after reboot:
- semantic proof applied remains **3**;
- pending semantic queue becomes **23**, matching the post-AI resumable state.

Other project metrics should remain stable.


## End-of-day green checkpoint — 2026-09-29

Final live Streamlit validation after reboot on the saved 12-document DSK project.

### Stable project state

Knowledge / routing:
- normative documents: 13;
- validity records: 153;
- atomic requirements: 86;
- verified clauses: 57;
- executable contracts: 57.

Normative execution:
- evidence candidates: 120;
- proved: 11;
- held by proof control: 33;
- semantic proof applied: 3;
- pending semantic queue: 23;
- specialist questions: 43;
- system limitations: 3;
- addressable evidence: 73.7%.

### What is now proven in the live product

1. Semantic proof survives Streamlit reboot.
2. Semantic proof survives knowledge expansion when the judged requirement and selected
   addressable evidence are unchanged.
3. Semantic proof survives retrieval candidate-pool growth/re-ranking when the selected
   evidence remains unchanged.
4. Changed selected evidence or changed requirement still invalidates proof fail-closed.
5. Alpha 10 resumable queue is aligned with selected-evidence reuse:
   processed packets no longer return to pending after reboot solely because the root queue
   fingerprint changed.
6. Cross-document retrieval can reserve evidence capacity for a different section/source
   without bypassing the evidence-quality layer.
7. Current Test78 remains stable at 27/56 categorical:
   25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW, NO_CHANGE.

### End-of-day decision

Stop development for the day at this checkpoint.

Do not:
- re-upload the 12 PDFs;
- run another full-project AI pass;
- add normative wave 4 on top of this state today.

Next session:
- start from this green checkpoint;
- keep the same saved DSK project as the control project;
- begin normative knowledge wave 4 only after confirming the branch is still at or
  descended from this checkpoint.


## Validated checkpoint — normative knowledge wave 4: SPZ power and fire-water systems

Source commit:
`fb5ccae946b16024f5163df8f96d8c9d12adbd4c`

### Scope

Knowledge-only expansion. Core verdict logic was not changed.

Catalogue after wave 4:
- normative documents: 16;
- validity records: 154;
- atomic requirements: 93;
- newly added verified clauses in this wave: 7.

Documents curated in wave 4:
- SP 6.13130.2025 — low-voltage electrical installations / fire-protection-system power;
- SP 8.13130.2020 — outdoor fire-water supply;
- SP 10.13130.2020 — indoor fire-water supply.

Edition transition:
- historical SP 6.13130.2021 validity record is preserved and marked replaced;
- replacement: SP 6.13130.2025;
- replacement effective from 29.06.2026.
This edition transition is stored as normative validity data and is not by itself treated as
a project finding; applicability to a project/document must consider the relevant project
and document dates.

Verified atomic clauses added:
- SP 6.13130.2025 cl. 5.2 — reliability category for fire-protection-system electric receivers;
- SP 6.13130.2025 cl. 5.3 — fire-protection-system power supply from the dedicated SPZ panel/NKU for applicable I-category objects;
- SP 8.13130.2020 cl. 10.2 — calculation basis for fire-water storage volume;
- SP 8.13130.2020 cl. 10.3 — minimum number of fire-water reservoirs and distribution of fire-water reserve;
- SP 8.13130.2020 cl. 11.5 — water-level measurement/control in fire-water reservoirs;
- SP 10.13130.2020 cl. 1.4 — justification of cases where indoor fire-water supply is not required;
- SP 10.13130.2020 table 7.2 — indoor fire-water demand for production/warehouse buildings.

Full normative texts were not copied into the repository. The knowledge package stores
source metadata, clause addresses, paraphrased atomic requirements and proof contracts.

### Regression control

At `fb5ccae9...`:
- Core20 tests: success;
- results-integrity: success;
- Core20 regression: success;
- Core25 tests: success;
- baseline full diagnostic: success;
- alpha1 release gate / full legacy suite: success;
- Test78: success / NO_CHANGE;
- Test78 remains 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

### Live baseline before wave 4

Saved 12-document DSK project:
- executable contracts: 57;
- evidence candidates: 120;
- proved: 11;
- semantic proof applied: 3;
- pending semantic queue: 23;
- specialist questions: 43;
- system limitations: 3;
- addressable evidence: 73.7%.

### Next validation

Use the same saved DSK project.
Do not re-upload PDFs and do not run AI before taking the first wave-4 measurement.

Primary checks:
- the existing 3 semantic confirmations remain applied;
- verified-clause routes / executable contracts increase by the newly applicable wave-4 clauses;
- fire-water clauses should find addressable evidence in IOS2 where the project describes
  fire-water reserve, three reservoirs and level control;
- SPZ-power clauses should route to IOS1/PB evidence without creating a categorical result
  merely from a normative reference.

Record:
- executable contracts;
- evidence candidates;
- proved;
- held by proof control;
- semantic proof applied;
- pending semantic queue;
- specialist questions;
- system limitations;
- addressable evidence.


## Validated checkpoint — wave 4 fire-water correction and TOC evidence-quality fix

Validated lineage:
- wave 4 green checkpoint: `6019b8b9087866f334b14a03f047571704b2f2a8`;
- corrected SP 8 knowledge: `3d4b798b0dcd573bd80f69c1a0356e212de0e53e`;
- narrative-table / design-assignment TOC fix: `1e7ec745a118fcd7f26fe3aabe2edd99b907ef5d`.

### Wave-4 diagnosis on the saved DSK corpus

The first wave-4 live measurement was:
- executable contracts: 64;
- evidence candidates: 140;
- proved: 11;
- held by proof control: 38;
- semantic proof applied: 3;
- pending semantic queue: 28;
- specialist questions: 50;
- system limitations: 3;
- addressable evidence: 75.0%.

Five of seven wave-4 clauses reached semantic proof. Two SP 8 clauses did not:
- old SP8-10.2-FIRE-WATER-VOLUME -> weak evidence;
- old SP8-10.3-FIRE-RESERVOIRS -> positive evidence not found.

Manual review showed that section 10 of SP 8 is the direct fire-reservoir / fire-pond
scenario, while the DSK design uses reservoirs feeding a fire-pump station and an outdoor
fire-water network with hydrants. For this architecture the relevant verified section is
section 9 "Water storage tanks":
- cl. 9.2 — fire-water volume in water-supply-system reservoirs;
- cl. 9.5 — at least two reservoirs, at least 50% remaining fire-water volume when one
  reservoir is disabled, and independent operation/emptying.

The DSK IOS2 corpus contains strong addressable evidence:
- IOS2 sheet 13 / PDF page 14 — internal/outdoor fire-flow basis, 270 m3 reserve, three
  100 m3 reservoirs, pump station and outdoor fire-water scheme;
- IOS2 sheet 19 / PDF page 20 — explicit calculation V = 25 x 3.6 x 3 = 270 m3 and
  3 x 100 m3 reservoirs;
- IOS2 sheets 23-24 / PDF pages 24-25 — automatic level measurement, reserve level
  control and dispatcher signalling.

Wave 4 knowledge therefore replaces the two section-10 contracts with:
- SP8-9.2-WATER-SYSTEM-FIRE-VOLUME;
- SP8-9.5-WATER-SYSTEM-RESERVOIRS.

SP10 cl. 1.4 and table 7.2 remain in the package, but their topic/keywords were tightened
toward internal fire-water evidence.

### Evidence-quality root cause

IOS2 PDF page 14 was incorrectly classified as a table-of-contents page.

The old TOC detector could classify a page as TOC based on dense numbered entries and
chained numeric references even when:
- no standalone "Содержание"/"Оглавление" heading existed;
- no dot leaders/page references existed;
- the page contained a substantive table followed by engineering narrative.

It could also treat the design-assignment column heading
"Содержание основных данных и требований" as an explicit contents heading.

The corrected detector:
- recognises "Содержание"/"Оглавление" only as standalone headings;
- keeps dot leaders + page references as the strong TOC signal;
- requires a much denser combined continuation-page pattern when the heading/leaders are
  absent;
- no longer treats ordinary engineering tables or design-assignment content columns as TOC.

Regression tests explicitly cover:
- TOC continuation without the heading;
- standalone explicit contents heading;
- design-assignment "Содержание основных данных и требований" as non-TOC;
- a tabular fire-water page with substantive narrative as non-TOC.

### Validation

At current source `1e7ec745...`:
- Core20 tests: success;
- results-integrity: success;
- Core20 regression: success;
- Core25 tests: success;
- baseline full diagnostic: success;
- alpha1 release gate / full legacy suite: success;
- Test78: success / NO_CHANGE;
- 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

### Next Streamlit check

Use the same saved 12-document DSK project.
Do not re-upload PDFs and do not run AI.

Compare against the pre-correction wave-4 live baseline:
64 contracts / 140 evidence candidates / 11 proved / 38 held /
3 semantic proof applied / 28 pending / 50 specialist questions /
3 system limitations / 75.0% addressable evidence.

Expected qualitative checks:
- the existing 3 semantic confirmations remain preserved if their selected evidence is unchanged;
- SP8 cl. 9.2 and 9.5 should now reach addressable semantic evidence instead of stopping
  before semantic proof;
- SP10 cl. 1.4 / table 7.2 should be able to use the substantive IOS2 fire-water page rather
  than being forced toward noisier KR evidence;
- design-assignment pages should no longer be rejected solely because their table header
  contains the word "Содержание".


## Live green checkpoint — wave 4 corrected fire-water routing

Validated in Streamlit on the same saved 12-document DSK project after reboot, with no PDF
re-upload and no new AI run.

### Live metrics after SP 8 / TOC correction

Compared with the pre-correction wave-4 baseline:

- executable contracts: 64 -> 64;
- evidence candidates: 140 -> 154 (+14);
- proved: 11 -> 11;
- held by proof control: 38 -> 40 (+2);
- semantic proof applied: 3 -> 3;
- pending semantic queue: 28 -> 30 (+2);
- specialist questions: 50 -> 50;
- system limitations: 3 -> 3;
- addressable evidence: 75.0% -> 78.1% (+3.1 pp).

### Interpretation

The correction improved the evidence layer rather than inflating the normative scope:
- no additional executable contracts were created;
- addressable evidence increased materially;
- two additional requirements reached semantic proof instead of stopping earlier;
- the existing three selected-evidence semantic confirmations survived the knowledge and
  retrieval changes;
- no new deterministic/categorical result appeared solely from the correction.

This aggregate result is consistent with the intended correction:
- SP 8 section 9 clauses replace the previously mismatched section 10 clauses for the
  reservoir -> fire pump station -> outdoor fire-water network architecture;
- substantive IOS2 table/narrative pages are no longer excluded as TOC;
- design-assignment table headers containing "Содержание основных данных и требований" no
  longer trigger TOC rejection by themselves.

### Next step

The wave-4 evidence/routing correction is accepted as green.

Run one bounded normative semantic batch only; do not run the full-project AI pipeline.
Record post-AI values for:
- proved;
- semantic proof applied;
- pending semantic queue;
- specialist questions;
- evidence candidates;
- addressable evidence.

Provider rate limits may stop the batch early; completed semantic decisions must remain
persisted and resumable.


## Validated checkpoint — partial semantic run after expanded normative root

Source commit:
`b057f33a65671d39f60306b5a1618ff96d4f0579`

### Live symptom after corrected wave 4 AI run

Pre-run:
- contracts: 64;
- evidence candidates: 154;
- proved: 11;
- held by proof control: 40;
- semantic proof applied: 3;
- pending semantic queue: 30;
- specialist questions: 50;
- system limitations: 3;
- addressable evidence: 78.1%.

After one bounded semantic run stopped by provider rate limit:
- contracts: 64;
- evidence candidates: 154;
- proved: 12;
- held by proof control: 40;
- semantic proof applied: 4;
- pending semantic queue: 30;
- specialist questions: 49;
- system limitations: 3;
- addressable evidence: 78.1%.

One new requirement was clearly confirmed, but pending did not decrease.

### Root cause class

Alpha 10.1 already handled:
- resumable runs on one unchanged root;
- selected-evidence reuse across retrieval changes;
- fail-closed return of stale packets to pending.

The uncovered case is different:
1. knowledge/retrieval expansion increases the full normative root;
2. apply() safely removes reusable completed decisions;
3. the Streamlit button receives only the already-filtered pending slice;
4. that pending slice can itself be larger than the historical root total;
5. run() may then treat the pending slice as a new standalone root and fail to carry forward
   previously completed decisions that are absent from the slice.

With a partial provider run this can make one newly completed decision replace previously
processed checkpoint state instead of strictly accumulating it.

### Fix

The resumable run now distinguishes:
- unchanged complete-root calls: previous completed decisions are skipped and accumulated as before;
- pending-slice calls after root expansion: only previous completed decisions whose
  requirement IDs are absent from the current pending slice are carried forward.

A previous decision whose requirement ID is present in pending is deliberately not carried.
It must be re-evaluated fail-closed.

The merged root total for an expanded pending slice is reconstructed as:
current pending packets + safely carried completed decisions.

### Regression coverage

Added tests verify:
- an expanded pending slice larger than the old root total preserves prior completed
  VERIFIED and REVIEW decisions while accumulating a new partial-run decision;
- provider 429 does not erase already completed decisions;
- a previous decision whose requirement is pending again is not silently carried forward.

### Validation

At `b057f33a...`:
- Core20 tests: success;
- results-integrity: success;
- Core20 regression: success;
- Core25 tests: success;
- baseline full diagnostic: success;
- alpha1 release gate / full legacy suite: success;
- Test78: success / NO_CHANGE;
- 25 VERIFIED_OK + 2 PROJECT_FINDING + 29 REVIEW = 27/56;
- changed requirement IDs: none.

### Next live validation

The already-persisted checkpoint from the previous partial run cannot reconstruct decisions
that were not stored in it, so reboot alone may still show:
- semantic proof applied: 4;
- pending semantic queue: 30.

Do not interpret that as failure of this fix.

After provider availability returns, run exactly one more bounded normative semantic batch.
The success criterion is:
- existing completed decisions remain preserved;
- each newly completed packet decreases pending rather than replacing prior checkpoint state;
- provider failure leaves unfinished packets pending without deleting completed decisions.


## Live validation — resumable semantic queue confirmed after expanded-root fix

Validation date: 2026-10-01.

Validated source checkpoint before the live run:
`be5af9e60acd96aca0ff9ba1afb128fb547d9b2b`

Relevant fix:
`b057f33a65671d39f60306b5a1618ff96d4f0579` — `normative: preserve completed decisions across expanded pending roots`

### Pre-run state

- contracts: 64;
- evidence candidates: 154;
- proved: 12;
- held by proof control: 40;
- semantic proof applied: 4;
- pending semantic queue: 30;
- specialist questions: 49;
- system limitations: 3;
- addressable evidence: 78.1%.

### Post-run state

After exactly one bounded live semantic run:

- contracts: 64;
- evidence candidates: 154;
- proved: 15;
- held by proof control: 40;
- semantic proof applied: 7;
- pending semantic queue: 26;
- specialist questions: 46;
- system limitations: 3;
- addressable evidence: 78.1%.

Delta:

- proved: +3;
- semantic proof applied: +3;
- pending semantic queue: -4;
- specialist questions: -3.

### Result

The expanded-root resumable-queue fix is confirmed in the live project state.

The critical acceptance criterion passed: the pending queue decreased from 30 to 26 while previously completed semantic decisions remained accumulated. Four newly completed packets were consumed from the pending queue; three of them promoted requirements to semantic VERIFIED_OK, while one completed without an additional VERIFIED_OK promotion.

This confirms that a new partial semantic run now accumulates completed decisions on top of the persisted checkpoint instead of replacing earlier completed state.

### Next development target

Do not spend the next iteration on resumable-checkpoint mechanics unless a regression appears.

The next quality investigation should focus on the remaining:
- 26 pending semantic packets;
- 40 contracts held by proof control;
- 46 specialist questions.

First separate those populations by machine-readable reason code and proof state, then identify whether the dominant blockers are:
1. missing/weak addressable evidence;
2. incomplete requirement/evidence binding;
3. semantic ambiguity requiring Judge/Critic;
4. missing normative knowledge;
5. genuine project-side uncertainty.

Preserve Test78 and the current live metrics as non-regression baselines.


## Checklist profiles foundation — PD/RD reference integration

Development date: 2026-10-05.

Reference source:
- RAM project-documentation checklist (PD): 571 questions / 20 disciplines;
- RAM working-documentation checklist (RD): 296 questions / 13 disciplines.

### Architectural decision

The new PD/RD checklists are not merged into the legacy `knowledge/checklist_catalog.json`.
The legacy catalog remains unchanged and continues to drive the existing automatic checklist router.

The new checklists are stored as independent canonical stage profiles:
- `knowledge/checklist_profiles/pd.json`;
- `knowledge/checklist_profiles/rd.json`.

This prevents duplicate rules, keeps the existing 761-row corporate catalog stable, and allows
the application to select exactly one stage profile when the project/documentation stage is known.

### Core contract added

Checklist atomic verification now supports:
- stable namespaced parent IDs for stage profiles:
  - `CHECK-PD-0001`;
  - `CHECK-RD-0001`;
- unchanged legacy sequence IDs when no profile is supplied;
- checklist profile metadata on every atomic condition;
- checklist priority and criteria propagation;
- multiple expected evidence sections per checklist item;
- duplicate parent-ID rejection instead of silent overwriting.

Review-plan construction now preserves:
- `checklist_parent_id`;
- `checklist_profile`;
- priority;
- criteria;
- multi-section evidence routes.

### Canonical profile registry

Added `core/checklist_profiles.py`.

The registry validates:
- profile code;
- unique positive question IDs;
- priority in {1, 2, 3};
- non-empty discipline and question;
- declared question count;
- normalized multi-section evidence routes.

Static source validation after import:
- PD: 571 unique IDs, 20 disciplines, priorities P1=206 / P2=364 / P3=1;
- RD: 296 unique IDs, 13 disciplines, priorities P1=109 / P2=182 / P3=5;
- empty criteria: 0;
- broken linked/dependency references: 0.

Intentionally unresolved routing remains fail-closed:
- PD: Общие решения, ОПО Промбез, ТБЭ, Энергоэффективность;
- RD: Общие требования, Финальная проверка.

These groups must not be mapped to arbitrary project sections.

### Commits

- `be0264d203403a462f98d59e93593993bf343e02` — checklist: preserve PD/RD profile identity and evidence routes
- `e87420bd0659c08c45446c8f37ef284bff87d75e` — test: lock PD/RD checklist profile contract
- `ddc76297260409a2d38a874f18c033cf43538da6` — checklist: add PD canonical profile
- `efa6da106e416a4b2d1edbef51bdb070a8b34d1c` — checklist: add RD canonical profile
- `daebba8b1d2cb042f9e3fb04e675313f6f52f4db` — checklist: add PD/RD profile registry
- `2c3b0a14750c2130b47058cdd774699384ff7b83` — test: validate canonical PD/RD profiles
- `f5f57304f20d021c2f8d9b9f3209ca96deef2ed3` — checklist: preserve profile trace in review plan
- `01e9ef359f0e5094641c70f440a5ef201f554bb1` — test: preserve checklist profile trace in review plan

### Validation state

Static profile validation passed. GitHub combined status currently exposes no CI statuses for
the latest commits through the connector, so this checkpoint must not yet be called green.

No existing runtime path automatically activates PD or RD profiles yet. This is intentional:
the current ExpertCheck behavior and Test78 baseline are not changed by the profile data itself.

### Next development target

Add an explicit documentation-stage selection (PD / RD) to the project setup and carry that
selection into the analysis runtime. Then activate exactly one canonical checklist profile and
run a bounded regression before allowing profile results into public readiness metrics.

Do not activate PD and RD simultaneously by default.


## Checklist stage routing — explicit PD/RD project context

Development date: 2026-10-05.

The project setup now has an explicit documentation-stage selector:
- ПД — project documentation;
- РД — working documentation.

The UI maps the selected stage to exactly one canonical checklist profile:
- ПД -> PD;
- РД -> RD.

The stage is carried through the existing `ai_options` runtime contract into
`analyze_uploaded_core`, where it is normalized and attached to project context and
lightweight document metadata.

### Persistence

`documentation_stage` is now part of:
- application session defaults;
- new-project reset state;
- workspace session payload;
- workspace autosave signature;
- project open/restore defaults;
- portable project snapshot export and restore.

Changing the project stage therefore changes the workspace signature and is persisted.

### Runtime safety

The selected profile is currently recorded in `automatic_checklist_review.profile_selection`
with state `REGISTERED_NOT_ACTIVATED`.

The canonical profile summary is loaded and validated, but its 571/296 checklist questions
are intentionally not merged into:
- `automatic_checklist_review.results`;
- `project_review_plan`;
- coverage/readiness metrics;
- report Quality Gate.

This preserves the current Test78 and live-project baseline while the stage-selection path is
validated.

### Commits

- `21985ab011cec5a102aebd8f14ba7b342fb28141` — checklist: persist documentation stage in app session
- `fb9a3062e1b5e406cbfc7ce18852e75e89233fdf` — workspace: persist documentation stage
- `ab68be4d2cf28a0937d355fb649584ebc968a970` — workspace: restore documentation stage default
- `b465a4443bfd7bd3edec530310b917fe667aba78` — ui: add explicit PD/RD documentation stage
- `b2cb849d4c84c66c38d8671a1cbc65e2ddda976b` — pipeline: carry PD/RD stage without activating profile metrics
- `4a15ed4e19450f22bbf09f06698686136cde7011` — test: persist PD/RD documentation stage
- `6354dfe51e8b7aa873e7e39cc3936c818f9c7cad` — ui: make review mode guidance stage-aware
- `586d4203415335d777538108f7b937a082a12755` — snapshot: preserve PD/RD documentation stage

### Validation state

Source/diff inspection passed:
- branch is ahead of the prior checklist checkpoint only by the expected stage-routing files;
- stage-specific UI text is present;
- pipeline normalization accepts only PD/RD;
- workspace stage participates in the autosave signature;
- snapshot restore has a safe PD fallback for older snapshots.

GitHub combined commit status remains empty and there is no open PR for the branch.
Therefore this checkpoint is not labelled green.

### Next target

Build a bounded shadow execution of the selected canonical profile:
1. run exactly one selected profile, never PD+RD together;
2. keep shadow results outside public readiness metrics;
3. measure atomic expansion, deterministic completion, candidate evidence, runtime and snapshot size;
4. only after regression validation decide how profile results enter the public checklist ledger.


## Normative knowledge expansion — GOST R 21.101-2026 wave 1

Development date: 2026-10-05.

### Baseline preserved

The verified live normative baseline before this wave remains:
- active contracts: 64;
- proved: 15;
- held by proof control: 40;
- semantic proof applied: 7;
- pending semantic queue: 26;
- specialist questions: 46;
- system limitations: 3;
- addressable evidence: 78.1%.

The purpose of this wave is to grow the curated NTD knowledge base without automatically
inflating the active project denominator or specialist-question queue.

### Knowledge-base split

Before this wave:
- total normative rules: 75;
- strict verified/categorical contracts: 64;
- clause-verification backlog: 11.

After this wave:
- normative rules: 77;
- strict registered contracts: 66;
- triggered-only contracts: 2;
- default active contract pool: 64;
- clause-verification backlog: 11 (PP87: 10; 384-FZ: 1).

This introduces an explicit distinction between:
1. registered verified NTD knowledge;
2. contracts active for a concrete project run.

### GOST R 21.101-2026 status

The document/status registry and validity registry were refreshed:
- GOST R 21.101-2026: active from 2026-04-01;
- replaces GOST R 21.101-2020;
- current trace includes the published correction IUS 11-2026;
- GOST R 21.101-2020 is recorded as replaced.

### New verified contracts

Added two clause-addressed contracts:
- `GOST21101-2026-7.3.1-CHANGE-NUMBER` — change number is assigned at document level;
- `GOST21101-2026-7.4.1-PD-INDEPENDENT-CHANGES` — PD document changes are performed independently within each document.

Both are `TRIGGERED_ONLY`.

A project with no addressable change marker does not receive these checks in:
- Core20 normative execution;
- legacy `NormativeComplianceEngine`;
- public review plan;
- semantic proof queue;
- readiness/coverage denominator.

When an addressable change marker is present, the clause is activated and proceeds through
the ordinary applicability/retrieval/proof contract.

### Runtime changes

Core20 normative execution now exposes:
- `registered_contracts`;
- `active_contracts`;
- `inactive_triggered_contracts`;
- `inactive_triggered_contract_rows`.

Normative foundation summary now separates:
- `automatic_contract_ready`;
- `triggered_only_contracts`;
- `default_active_contracts`.

Legacy normative compliance exposes the same activation audit through the pipeline summary.

Existing `CONDITIONAL` fail-closed semantics were preserved. Event-driven activation is a
new mode and does not weaken applicability handling for fire/mining/other conditional clauses.

### Validation

Production checkpoint:
`cc983cd35942098d788ee1f5f5616619e3107c44`

GitHub Actions:
- Source Snapshot Artifact: success;
- Core20 quality gates: success;
- Core25 Quality Leap gates: success.

Test78 on the latest production-pipeline commit in this wave:
- classification: NO_CHANGE;
- baseline/current: 56 requirements;
- VERIFIED_OK: 25 -> 25;
- PROJECT_FINDING: 2 -> 2;
- REVIEW_QUESTION: 29 -> 29;
- changed IDs: none.

The earlier Core25 release-gate failure was traced to three checklist-profile tests using a
cwd-dependent `knowledge` path. The tests were repaired to use a repository-root absolute
fixture path. Core25 then returned to success; checklist production behavior was not changed.

### Key commits

- `3cd858384f76b0efc7701401c166f3b4752cd7cf` — verify GOST R 21.101-2026 status
- `c8aeb59b221ee4de3cc427278fbc32b4bde1ac35` — refresh GOST 21.101 validity trace
- `c47a3f9588ad7b6501bb664c74a7262ea9492337` — add GOST 21.101-2026 change contracts
- `d33bc72b4b687337d151711ca6abe487114a7cc6` — triggered-only Core20 activation
- `0e6ff359989ec6256514f08220bbc333a17a583a` — activate change clauses only on change evidence
- `d372a26639124641c8741a138416c7e0f7681e9f` — triggered-only legacy ledger
- `b9f1af9b9fc8665e9f1b307697763445ccb86bde` — expose activation audit in pipeline
- `e1cb82894cf9492c83ece76659492a708b54ce57` — fix cwd-independent checklist test fixtures
- `9ed86f164d20fe30557cb957d3bc44dc04cd1f79` — separate registered/default-active summary
- `cc983cd35942098d788ee1f5f5616619e3107c44` — lock normative activation tests

### Next target

Do not add a large second NTD wave yet.

First validate the expanded foundation against the preserved live project:
1. registered strict contracts should become 66;
2. if the project has no actual document-change trigger, active contracts should remain 64;
3. existing 15 proved / 40 held / 26 pending / 46 specialist-question baseline must not worsen
   merely because the KB grew;
4. extract the existing `proof_frontier` diagnostic and rank the unresolved population by
   blocker/reason/source/section/evidence-admission state.

Then choose the next NTD clauses from the dominant real blocker/expert-history family rather
than expanding documents sequentially.


## Normative knowledge expansion — SP 48.13330.2019 wave 1 + compact frontier persistence

Development date: 2026-10-05.

### Purpose

Continue NTD expansion without returning to checklist development and without bulk-growing
the active normative denominator blindly.

Two connected improvements were made:
1. persist a compact, non-sensitive normative proof-frontier diagnostic for saved projects;
2. add one high-priority, expert-history-backed SP 48.13330.2019 clause.

### Compact normative diagnostic

Added `compact_normative_diagnostic()` to the Core20 dual-run layer.

The diagnostic persists only aggregate data:
- registered/active/inactive-triggered contract counts;
- VERIFIED_OK / PROJECT_FINDING / REVIEW_QUESTION / SYSTEM_LIMITATION counts;
- held-by-proof-control count;
- semantic/set/visual queue totals;
- evidence coverage percentage;
- proof-frontier blocker counts;
- semantic pending distribution by source, section, candidate-count bucket and retrieval admission;
- set-completeness distribution by source/section;
- visual pending distribution by kind/section;
- retained fail-closed distribution by reason/source/section.

It deliberately excludes:
- project text;
- evidence fragments;
- page excerpts;
- row-level proof packets;
- visual payloads.

The compact diagnostic is now:
- stored in session snapshot;
- part of the autosave signature;
- stored in new analysis history rows;
- backfilled into the latest existing history summary on ordinary project autosave when the
  analysis timestamp is unchanged and the old history row has no diagnostic yet.

This means an old saved project only needs to be opened in the updated application for the
current Core20 normative frontier to become queryable from the lightweight analysis history;
a new analysis run is not required.

### SP 48.13330.2019 selection

Expert-history priority:
- SP 48.13330.2019 appears in 173 verified remarks across 16 projects;
- it had no strict atomic contract before this wave.

The first clause was chosen from recurring real expert remarks, not by sequentially walking
through the standard.

Added:
- `SP48-5.16-SUPPLY-TRANSPORT-TEP`;
- source: SP 48.13330.2019, clause 5.16;
- route: POS;
- proof type: SEMANTIC_REQUIREMENT;
- policy: VERIFIED_ONLY.

The contract checks whether transport schemes for delivery of the principal construction
materials are justified by comparison of techno-economic indicators of supply alternatives.

Retrieval alone cannot close the clause. Semantic proof requires:
1. identifiable alternatives/supply options;
2. comparable techno-economic indicators;
3. traceable selection of the adopted supply/transport scheme based on the comparison.

The contract does not extend clause 5.16 to unrelated waste-transport claims merely because
historical expert remarks sometimes cite the clause in broader logistics comments.

### Knowledge metrics after this wave

- total knowledge rules: 96;
- normative rules: 78;
- strict registered normative contracts: 67;
- triggered-only contracts: 2;
- default-active strict contract pool: 65;
- clause-verification backlog: 11;
- SP 48.13330.2019 strict contracts: 1.

Compared with the previous checkpoint:
- strict registered: 66 -> 67;
- default-active pool: 64 -> 65;
- verification backlog: unchanged at 11.

### Validation

SP48 production contract commit:
`fbddec8eb285ef0c4b96dc2767bca9effb532d58`

Test78 deterministic A/B on that exact NTD commit:
- workflow: success;
- classification: NO_CHANGE;
- requirements: 56 -> 56;
- VERIFIED_OK: 25 -> 25;
- PROJECT_FINDING: 2 -> 2;
- REVIEW_QUESTION: 29 -> 29;
- changed IDs: none.

Final test checkpoint:
`daf3c3ac48b5fb96add61dbe4df974fed6ca9a44`

GitHub Actions on final checkpoint:
- Source Snapshot Artifact: success;
- Core20 quality gates: success;
- Core25 Quality Leap gates: success.

### Expert-history rationale for next candidates

The expert-practice corpus shows repeated POS/logistics comments tied to SP 48:
- transport schemes and supply-source justification;
- techno-economic comparison of alternative suppliers/routes;
- construction-duration/source-data consistency;
- shift/rotational-work assumptions and cost/logistics justification;
- graphical completeness of POS.

Next SP 48 candidates remain:
- clause 5.14 — justification that organisational/technological decisions account for all
  associated works/costs in estimate documentation;
- clause 5.15 — comparison of techno-economic indicators of competitive organisational/
  technological alternatives;
- clause 9.3.1 — NTS for non-standard design and organisational-technological solutions.

Do not add these clauses until the compact frontier from the preserved live project has been
backfilled and ranked.

### Next target

Open the preserved project in the updated application (no new analysis required), allow
autosave to backfill the compact normative diagnostic, then query the latest analysis history
summary from Supabase.

Use that live frontier to decide whether the next improvement should target:
- semantic proof throughput;
- set completeness;
- visual proof;
- applicability;
- or another NTD family.

Checklist PD/RD work remains paused.


## Semantic proof frontier — live Test for drawing reading

Development date: 2026-10-05.

### Preserved live benchmark

Project:
- `Тест для чтения чертежей`
- analysis timestamp: 2026-10-02T10:55
- compact diagnostic version: 1.1

Live normative frontier after opening the saved project:
- registered contracts: 66;
- active contracts: 66;
- VERIFIED_OK: 10;
- PROJECT_FINDING: 0;
- REVIEW_QUESTION: 51;
- SYSTEM_LIMITATION: 5;
- held by proof control: 43;
- semantic pending: 47;
- semantic completed: 0;
- set completeness pending: 3;
- visual pending: 5;
- evidence coverage: 89.4%.

The triggered GOST R 21.101-2026 change-number contract is active in this project,
so active=registered=66 for this saved snapshot.

### Exact semantic frontier

All 47 semantic-pending requirement IDs are now persisted in compact diagnostic
without project text or evidence fragments.

Retrieval quality:
- STRICT_RETRIEVAL: 38;
- STRONG_NEAR_MISS: 6;
- WEAK_RETRIEVAL: 3;
- 29 requirements have 4+ evidence candidates;
- 24 requirements combine STRICT_RETRIEVAL with at least 4 addressable candidates.

Semantic proof contracts:
- Gate 2.0 / explicit semantic contract configured: 3;
- no explicit semantic proof contract yet: 44.

Configured semantic contracts in the current frontier include:
- FZ384-15-2-RESP-INPUT;
- FZ384-15-5.1-SAFETY-JUSTIFICATION;
- GOST21101-2026-7.3.1-CHANGE-NUMBER.

This means the dominant bottleneck is no longer retrieval coverage. It is semantic
proof throughput and proof-contract depth.

### Resumable semantic proof architecture

Confirmed that resumability already belongs to the Alpha 10.1 reliability overlay
(`core20/alpha10_reliability.py`), installed from `core20/__init__.py`.

The lower `normative_semantic_proof.py` remains the base Judge/Critic engine.
Do not duplicate resumability there.

The Alpha 10.1 overlay now additionally supports:
- explicit optional checkpoint injection for deterministic tests/non-Streamlit callers;
- cumulative wave counters;
- completed/reviewed aliases exposed to compact diagnostics;
- live pending queue after accumulated decisions;
- frontier recomputation after stored proof is applied.

### Semantic wave prioritization

Semantic packets now carry non-sensitive retrieval quality metadata:
- retrieval kind;
- retrieval reason code;
- retrieval candidate count.

Bounded semantic waves are ranked before calling the base Judge/Critic engine:
1. STRICT_RETRIEVAL;
2. STRONG_NEAR_MISS;
3. WEAK_RETRIEVAL;
4. within the same admission tier, explicit Semantic Gate 2.0 first;
5. then larger addressable evidence candidate count.

The root queue fingerprint and verdict policy are unchanged. Ranking changes only
which pending requirements are attempted first.

For the current 47-item live frontier, the first 24-item wave contains:
- 24 STRICT_RETRIEVAL requirements;
- 0 STRONG_NEAR_MISS;
- 0 WEAK_RETRIEVAL.

Wave 1 starts with:
- FZ384-15-5.1-SAFETY-JUSTIFICATION;
- SP8-9.5-WATER-SYSTEM-RESERVOIRS;
- SP8-9.2-WATER-SYSTEM-FIRE-VOLUME;
- SP8-11.5-FIRE-WATER-LEVEL;
- SP6-2025-5.3-SPZ-PANEL;
- SP6-2025-5.2-SPZ-RELIABILITY;
then other strict 4-candidate requirements.

### Validation

Functional priority commit:
`18a17856cffbb27dd82dbccae505718a43f07ebc`

Final regression-test commit before this documentation checkpoint:
`ad1b478dd7d0637152ecd47b510163295144c5d9`

Validation:
- Core20 quality gates: success;
- Core25 Quality Leap gates: success;
- Streamlit startup smoke on functional commit: success;
- Test78 deterministic A/B on functional commit: success;
- Test78 classification: NO_CHANGE;
- baseline/current: 56 requirements, 25 VERIFIED_OK, 2 PROJECT_FINDING, 29 REVIEW_QUESTION;
- changed IDs: none.

### Next live action

Refresh/open `Тест для чтения чертежей` on the deployed priority build and run
one bounded semantic proof wave (up to 24 packets) using independent Judge and Critic.

After autosave:
1. read compact diagnostic from Supabase;
2. compare 10/47/51 baseline with post-wave state;
3. classify completed semantic decisions into VERIFIED_OK versus reviewed-no-promotion;
4. inspect remaining pending IDs;
5. add Semantic Gate 2.0 contracts only where live results show they are needed.

Do not add more NTD clauses before this live semantic wave is analyzed.
Checklist PD/RD work remains paused.


## Semantic proof live wave 1 — 2026-10-05

Project: `Тест для чтения чертежей`.

Baseline before wave:
- VERIFIED_OK: 10;
- semantic pending: 47;
- REVIEW_QUESTION: 51;
- held by proof control: 43.

Wave request:
- selected: 24 prioritized packets;
- priority policy: STRICT_RETRIEVAL first.

Actual completed decisions: 4.
- `SP8-9.5-WATER-SYSTEM-RESERVOIRS` → VERIFIED_OK;
- `SP8-9.2-WATER-SYSTEM-FIRE-VOLUME` → VERIFIED_OK;
- `SP8-11.5-FIRE-WATER-LEVEL` → VERIFIED_OK;
- `FZ384-15-5.1-SAFETY-JUSTIFICATION` → REVIEW_QUESTION.

Post-wave state:
- VERIFIED_OK: 13;
- semantic pending: 43;
- REVIEW_QUESTION: 48;
- held by proof control: 40;
- semantic completed total: 4;
- semantic reviewed without promotion: 1.

Provider failures:
- RATE_LIMIT: 2;
- SERVER_ERROR: 1.

The remaining 20 selected packets were not rejected; the provider circuit breaker
stopped the wave before they received complete decisions. Resumability preserved
the four completed decisions and the remaining queue.

For `FZ384-15-5.1-SAFETY-JUSTIFICATION`:
- Judge verdict: SUPPORTS;
- Critic: accepted;
- independent models: yes;
- Semantic Contract Gate 2.0: blocked;
- missing group: `Обоснование соответствия относится к проектным решениям`.

Do not weaken this semantic contract without inspecting the selected evidence.
The deterministic gate correctly overruled the AI promotion.

Compact diagnostic version: 1.3.
Diagnostic now exposes only safe provider failure categories and safe semantic
gate group labels; no project text/model explanations are persisted in summary.

Next live action:
- run one more resumable semantic wave after provider rate-limit recovery;
- the four completed decisions must be skipped;
- analyze the new completed/pending delta before changing retry policy or adding NTD.


## Deterministic normative proof expansion — owner-scoped wave

Development date: 2026-10-05.

### Direction

ExpertCheck keeps deterministic proof as the primary normative path:
1. verified NTD clause;
2. applicability;
3. addressable retrieval;
4. deterministic proof contract where the requirement is formalizable;
5. Semantic Gate / independent Judge-Critic only for the genuine semantic remainder.

The live semantic runs confirmed that provider reliability is not a suitable primary
proof mechanism. AI remains a residual layer, not the normative engine.

### Deterministic responsibility-level proof

Requirement:
- `FZ384-4-7-RESP-LEVEL`

Changed from generic semantic proof to positive deterministic presence:
- `check_kind=PRESENCE`;
- `execution_mode=POSITIVE_PRESENCE_ONLY`.

Positive addressable evidence that establishes one lawful responsibility level may
close the requirement without AI. Missing evidence never creates a project finding.

Registry commit:
- `5406d2f4bfb4dbd68848febde6021cfdc042891d`

Regression commit:
- `fe1a5334bacbc4ecc1a00f8f68f7f2f76cd4f957`

Validation:
- Core20: success;
- Core25 release gate: success;
- Test78: NO_CHANGE, 56 requirements, 25 VERIFIED_OK / 2 PROJECT_FINDING / 29 REVIEW,
  changed IDs none.

### Owner-scoped SET_COMPLETENESS

A safety gap was found in generic set completeness: section-scoped evidence could
theoretically satisfy different required elements using pages belonging to different
objects in a multi-object project.

Normative execution now supports:
- `set_contract.owner_scope=SAME_CONFIRMED_OBJECT`.

The owner index is built only from evidence already admitted into
`documents[0].project_understanding`, therefore it inherits:
- stable Project Understanding `object_id`;
- owner-lineage checks;
- scope binding;
- Fact Admission Gate.

Rules:
- all required set elements must be evidenced for the same confirmed object_id;
- evidence split across two objects does not close the set;
- a page mapped to more than one owner is ambiguous and cannot close the set;
- absent/ambiguous owner binding is fail-closed.

Core commits:
- `be85395743227909709ec1d169a18a9f874f87b3`
- `2332895e75471426be507a2929b5face1746b58a`

Regression commit:
- `bd05942cf719d198531fae4fe22aa69d1d0fe080`

Validation:
- two-object split is blocked;
- one confirmed owner closes the complete set;
- ambiguous owner page is blocked;
- Core20 and full Core25 release gate: success.

### Fire categorization without AI

Requirement:
- `FZ123-27-3-CATEGORY-BASIS`

Converted to owner-scoped deterministic `SET_COMPLETENESS`,
`DETERMINISTIC_AFTER_COMPLETE`.

Required elements:
1. kind and quantity of substances/materials, with a numeric quantity;
2. fire-hazard properties;
3. space-planning solutions;
4. characteristics of the technological process.

The complete set must belong to one confirmed Project Understanding object.

Registry commit:
- `9405016d7f1749c00f9e31945ad00d855e47b512`

Regression commit:
- `52c2ef9916420f8e480d397cf685ddb850a4364d`

Validation:
- one-owner complete set closes;
- cross-object evidence does not close;
- Core20 success;
- full Core25 success;
- Test78 NO_CHANGE.

Requirement:
- `SP12-4.2-CATEGORY-INPUTS`

Reuses the same owner-scoped categorization input set because the clause requires
the same formalizable evidence dimensions.

Registry commit:
- `bfc041b9813453f61e5c70b1d124bfb22b689cfe`

Regression commit:
- `88548528918a285a81d843258074c54642f99da9`

Validation:
- Core20 success;
- full Core25 release gate success;
- Test78 NO_CHANGE;
- Test78 baseline/current remains 56 requirements,
  25 VERIFIED_OK / 2 PROJECT_FINDING / 29 REVIEW, changed IDs none.

### Next proof archetype

Do not bulk-convert semantic contracts by topic/keyword.

Next target is a typed, owner-bound engineering proof archetype for requirements
that relate multiple structured properties. Candidate:
`GOST27751-10.1-CLASS-LEVEL-GAMMA`.

Before allowing automatic promotion:
- prove that class, responsibility level and reliability coefficient belong to
  the same confirmed object;
- implement typed value normalization and minimum-threshold mapping;
- explicitly hold special cases/exceptions unless applicability is proven;
- absence/conflict must remain REVIEW/SYSTEM_LIMITATION unless a dedicated
  machine-readable negative deviation contract exists.

Checklist work remains paused.
AI semantic proof remains a residual fallback.


## Deterministic normative proof expansion — 2026-10-05

Goal restored to the original product architecture:
- deterministic proof first;
- Semantic Gate second;
- Judge/Critic only for the irreducible semantic remainder.

### Live saved-project caveat

The saved project `Тест для чтения чертежей` still reports 43 semantic pending from
its 2026-10-02 analysis snapshot. Comparing those IDs with the current registry shows
that 8 of the 43 are now deterministic in the current codebase:

- FZ384-4-7-RESP-LEVEL → PRESENCE;
- PP87-12-K-TRANSPORT-PARAMS → SET_COMPLETENESS;
- FZ123-27-22-CATEGORY-IN-PD → PRESENCE;
- FZ123-27-3-CATEGORY-BASIS → SET_COMPLETENESS;
- SP18-5.52-CLOSED-STORM-SEWER → PRESENCE;
- SP52-7.6.1-EMERGENCY-LIGHTING-POWER → SET_COMPLETENESS;
- SP12-4.2-CATEGORY-INPUTS → SET_COMPLETENESS;
- SP6-2025-5.3-SPZ-PANEL → SET_COMPLETENESS.

Therefore the saved 43-item semantic queue is not a reliable representation of the
current normative engine. Do not keep feeding all 43 to AI without recomputation.

### New deterministic contract: SP52 7.6.1

`SP52-7.6.1-EMERGENCY-LIGHTING-POWER` was converted from semantic proof to an
ALL_REQUIRED deterministic set contract.

Required local evidence groups:
1. emergency lighting;
2. relation to failure/disconnection of working lighting;
3. automatic activation or manual activation after automation failure.

Promotion:
- `DETERMINISTIC_AFTER_COMPLETE`;
- no Judge/Critic needed;
- mere presence of the words “аварийное освещение” is insufficient.

Regression tests:
- complete local clause promotes to `DETERMINISTIC_SET_COMPLETENESS_PROOF`;
- presence-only text remains unproven.

### New deterministic contract: SP6 5.3

`SP6-2025-5.3-SPZ-PANEL` was converted to an owner-scoped deterministic set contract.

Required proof for the same confirmed Project Understanding object:
1. SPZ electric receivers are assigned I reliability category;
2. SPZ power is provided from the dedicated SPZ supply panel;
3. the panel belongs to / is implemented in NКУ.

Owner scope:
- `SAME_CONFIRMED_OBJECT`;
- evidence from different objects is never merged into one proof.

Regression tests:
- two evidence pages mapped to one object promote without AI;
- evidence split across two different objects remains unproven.

### Important correction caught by regression tests

`FZ384-4-7-RESP-LEVEL` was already a deterministic PRESENCE contract.
An attempted conversion to SET_COMPLETENESS was correctly rejected by the existing
regression suite. The exact pre-change contract was restored. This requirement must
not be reworked again unless a concrete false-positive case is demonstrated.

### Validation

Final functional/test head before this documentation checkpoint:
`5fd3cd3daabb15af4cd6966a1ad7c25a2fff8dcc`

Validation:
- Core20 quality gates: success;
- Core25 Quality Leap gates: success;
- full alpha1 release gate: success;
- Source Snapshot Artifact: success;
- Test78 deterministic A/B on the SP6 registry change: success;
- Test78 classification: NO_CHANGE;
- baseline/current: 56 requirements, 25 VERIFIED_OK, 2 PROJECT_FINDING, 29 REVIEW_QUESTION;
- changed IDs: none.

### Next course

Do not run another semantic AI wave yet.

Next development pass:
1. recompute the 35 still-semantic IDs against the current registry;
2. select only requirements with a truly formalizable proof contract;
3. prefer PRESENCE / SET_COMPLETENESS / typed or cross-document deterministic
   contracts where the engineering semantics can be made explicit;
4. leave threshold comparisons and conditional exceptions semantic until a typed
   comparison/applicability contract exists;
5. only after this reduction, use Judge/Critic on the residual semantic frontier.


## Deterministic normative proof expansion — typed numeric archetype — 2026-10-06

### Starting point

The previous checkpoint `01c07d63f3f54f36a87e42a5ac2ead2de08f35a3`
left 35 requirements from the 2026-10-02 saved semantic snapshot for
recomputation against the current registry. That 35-item list is a historical
frontier, not a live queue; do not feed it to AI without recomputation.

### PP87 p. 12 a(1) — ZOUIT disclosure

`PP87-12-A1-ZOUIT` was converted from SEMANTIC to PRESENCE.

Reason:
- the verified atomic requirement is disclosure of whether ZOUIT exist within
  the land-plot boundaries;
- an addressable positive statement that ZOUIT exist or an addressable statement
  that they are absent both satisfy the disclosure obligation;
- generic land-plot wording without ZOUIT does not close the requirement.

Result:
- proof path: `ADDRESSABLE_PRESENCE_PROOF`;
- no Judge/Critic is required.

Registry commit:
- `cceb9803f538113850c002c4cb4c546a8e2f5e8a`.

Regression commit:
- `6ad3ce2f920f58c349c73dd08e8b7deaf75c9843`.

### Reusable owner-bound typed numeric proof

A new deterministic typed archetype was added:
`OWNER_BOUND_PIECEWISE_MINIMUM`.

The evaluator:
1. extracts asserted engineering numeric values only near configured property aliases;
2. rejects normative comparator wording such as "не менее", "не более", "до",
   "свыше" so copied NTD clauses cannot become project evidence;
3. prefers the numeric value after the property label, preventing a neighboring
   property value on the same page from being attached to the wrong property;
4. binds selector and measured values through the confirmed Project Understanding
   owner index;
5. requires one evaluable confirmed object and refuses cross-object merging;
6. maps the selector into a declarative threshold band;
7. may promote only a positive PASS result;
8. holds below-threshold observations as REVIEW_QUESTION until a dedicated
   negative-deviation contract exists.

Core commits:
- `0691b5429a1d06bb4a344757fcae7919d81c72d2` — typed evaluator;
- `ed12be10e8b1361d364598df0f42a5e822668f64` — deterministic typed promotion;
- `51cc0fca64521030bcaab661341c744e63a152c2` — applicability remains fail-closed;
- `66c66436f2242911d0890fdddcb49996dd3ae61c` / `d0b0467b7d6d8c1077b00d91f7c9d74052c8ea10`
  — local property/value binding;
- `251b1516e100a7f88971865c2a27f80b02608718` — normalized numeric regex after
  PR validation exposed API escaping defects.

### First typed contract — SP 4 p. 8.2.3

`SP4-8.2.3-FIRE-ROAD-WIDTH` now uses TYPED_VALUE with the owner-bound
piecewise-minimum contract:

- object height <= 13 m -> fire-road width >= 3.5 m;
- object height > 13 m and <= 46 m -> width >= 4.2 m;
- object height > 46 m -> width >= 6.0 m.

The contract never turns absence or a below-threshold extraction directly into a
PROJECT_FINDING. Positive automatic promotion requires a unique confirmed owner,
an unambiguous object-height value, an addressable fire-road-width value and a
passing threshold comparison.

Registry commit:
- `50c5569dd695188cd50cb1e4a024a7e89614d8b4`.

Regression commits:
- `14473866c670bad8993d17f0ca845c302dd3eaf9`;
- `65b22eb87ff5010cdbf5cc2db7d2e38a517070d4`.

Coverage:
- same-owner positive PASS -> deterministic VERIFIED_OK;
- copied normative threshold text -> no promotion;
- below-minimum value -> REVIEW_QUESTION, never automatic finding;
- split owner evidence -> no promotion;
- same-page height and road width bind to their own post-label values.

### Validation

A temporary draft PR #8 was opened only to trigger pull-request validation against
a base branch pinned to checkpoint `01c07d63...`; it must not be merged.

Final validated functional head:
`251b1516e100a7f88971865c2a27f80b02608718`.

GitHub Actions:
- workflow: Core20 quality gates, run 919;
- conclusion: SUCCESS;
- core20-tests: 204 passed;
- results-integrity: SUCCESS.

The validation process caught two escaped-newline syntax defects from API writes and
then the doubled-regex escaping defect. All were repaired before the successful run.

### Updated frontier

The historical 35-item semantic frontier now contains at least two requirements
that are deterministic in current code:
- `PP87-12-A1-ZOUIT`;
- `SP4-8.2.3-FIRE-ROAD-WIDTH`.

Therefore the historical frontier is conceptually reduced from 35 to 33, but this
is NOT a live queue count. Recompute against the current registry before selecting
the next targets or running semantic AI.

Next recommended targets:
1. extend the typed archetype to piecewise ranges/maxima before touching complex
   formulas;
2. evaluate `SP4-8.2.6-ROAD-WALL-DISTANCE` and
   `FNP505-1215-CONVEYOR-CROSSING-SPACING`;
3. keep `SP18-5.37-ENTRANCE-GATE-WIDTH` held until a relative-formula contract
   (vehicle width + 1.5 m plus absolute minimum) exists;
4. keep `GOST27751-10.1-CLASS-LEVEL-GAMMA` held until special-case applicability
   and the gamma=1.2 override are explicitly modeled;
5. do not run another semantic AI wave before recomputation.


## Deterministic typed range expansion — 2026-10-06

This pass extends the first owner-bound numeric archetype without widening the
automatic negative-conclusion policy.

### Reusable piecewise range contract

`_typed_value_evaluation` now supports:
- `OWNER_BOUND_PIECEWISE_MINIMUM`;
- `OWNER_BOUND_PIECEWISE_RANGE`.

For a range contract:
- lower and/or upper bounds may be declared per selector band;
- all observed values for the same confirmed owner are evaluated through their
  minimum and maximum, so one convenient passing value cannot hide another
  out-of-range value;
- positive automatic promotion remains PASS-only;
- BELOW_MINIMUM / ABOVE_MAXIMUM / OUTSIDE_RANGE remain REVIEW_QUESTION and never
  become PROJECT_FINDING automatically.

Core commits:
- `1790dfcbd628dbe5b4cd62a673cd6474eeb8901c` — piecewise range support;
- `ca218d3b1a3616ed21fbe650e621d2455fd04a29` — explicit outside-range review;
- `c55bd8c463d193396765a7973957034ef2dfb1ca` — typed property labels require
  a local exact normalized alias, preventing separated token hits in copied NTD
  text from binding numbers to the wrong property.

### SP 4 p. 8.2.6

`SP4-8.2.6-ROAD-WALL-DISTANCE` was converted from SEMANTIC to TYPED_VALUE.

Owner-bound selector:
- object/building/structure height.

Measured property:
- distance from the fire-road edge / fire road / planned surface to the wall.

Piecewise contract:
- height <= 12 m -> distance <= 25 m;
- height > 12 m and <= 28 m -> distance 5–8 m;
- height > 28 m -> distance 8–10 m.

Registry commit:
- `feb87e273c35030d439c8a67f917692991a1d676`.

Regression commit:
- `7d21d5f09a17247302e6954e42dc7d073e04d54f`.

Coverage includes:
- positive middle-height band;
- upper-bound-only low-height band;
- out-of-range value remains specialist review;
- multiple observed distances must all satisfy the applicable range;
- copied normative range text cannot promote.

The copied-NTD regression initially exposed that generic retrieval-style
`_keyword_span_diagnostic` was too permissive for numeric property ownership.
Typed numeric extraction was therefore tightened to exact local aliases before
the final green run.

### Final validation

Final functional head for this pass:
`c55bd8c463d193396765a7973957034ef2dfb1ca`.

GitHub Actions:
- Core20 quality gates run 926: SUCCESS;
- Core20 regression: 209 passed;
- results-integrity: SUCCESS;
- Core25 Quality Leap gates run 630: SUCCESS;
- alpha1-release-gate: SUCCESS;
- Test78 deterministic A/B run 196: SUCCESS;
- Test78 classification: NO_CHANGE;
- Test78 baseline/current: 56 requirements,
  25 VERIFIED_OK / 2 PROJECT_FINDING / 29 REVIEW_QUESTION;
- changed requirements: 0;
- Streamlit startup smoke run 34: SUCCESS;
- Source Snapshot Artifact run 456: SUCCESS.

### Frontier after this pass

Relative to the historical 35-item semantic frontier identified from the
2026-10-02 saved project, three requirements are now deterministic in current code:
- `PP87-12-A1-ZOUIT`;
- `SP4-8.2.3-FIRE-ROAD-WIDTH`;
- `SP4-8.2.6-ROAD-WALL-DISTANCE`.

That makes the historical frontier conceptually 32 items, but it is still not a
live runtime queue count. Recompute the saved project against the current registry
before any semantic AI wave.

Recommended next proof work:
1. `FNP505-1215-CONVEYOR-CROSSING-SPACING` — likely typed piecewise maximum,
   but only after its categorical applicability/owner scope is represented;
2. `SP18-5.37-ENTRANCE-GATE-WIDTH` — needs a relative-formula contract
   (vehicle width + 1.5 m plus absolute minimum);
3. `GOST27751-10.1-CLASS-LEVEL-GAMMA` — keep held until the special-case
   gamma=1.2 override is modeled explicitly;
4. no semantic AI run before recomputation.


## Deterministic normative proof expansion — categorical typed conveyor spacing — 2026-10-06

### Goal

Continue reducing the historical semantic frontier without sending formalizable
engineering thresholds to AI.

### New typed archetype

Added `OWNER_BOUND_CATEGORICAL_RANGE`.

The contract:
- requires an explicit categorical selector; missing category never falls back to
  a more permissive band;
- binds selector and measured values to one confirmed Project Understanding owner;
- evaluates all observed numeric values for that owner against the selected range;
- promotes only positive PASS;
- selector conflicts, missing category, out-of-range values and ambiguous ownership
  remain REVIEW_QUESTION / structured-proof pending;
- never creates PROJECT_FINDING from an extracted out-of-range value without a
  dedicated negative-deviation contract.

Core commit:
- `5425c6cfcae22268b217ac5a1930d30d3ce34606`.

### FNP 505 p. 1215

`FNP505-1215-CONVEYOR-CROSSING-SPACING` was converted from SEMANTIC to TYPED_VALUE.

Selector categories:
- `INDOOR_OR_UNDERGROUND` — explicit building / underground-chamber placement;
- `OUTDOOR` — explicit open/outdoor placement.

Thresholds:
- indoor or underground -> crossing spacing <= 50 m;
- explicit outdoor placement -> crossing spacing <= 100 m.

Important fail-closed rule:
absence of indoor wording does NOT imply outdoor placement. The 100 m band requires
positive outdoor evidence.

Registry commit:
- `6dffb8e94ee184c3253e0186b896c35de87ea5dd`.

Regression commits:
- `9f461dddb34e6bb8b7946c5d60427f7b2d823279`;
- `03e66b38bfefdc8ea61aa223a7079847c2ef7422` — aligned the pre-existing conveyor
  retrieval regression with the new structured proof state.

Coverage:
- indoor 45 m -> deterministic VERIFIED_OK under 50 m band;
- explicit outdoor 80 m -> deterministic VERIFIED_OK under 100 m band;
- indoor 60 m -> REVIEW_QUESTION, never automatic finding;
- no explicit location category -> no promotion;
- conflicting indoor/outdoor category evidence -> no promotion;
- copied FNP threshold wording -> no promotion.

### Validation

Temporary draft PR #9 was used only to trigger validation and was closed without merge.

Final functional head:
`03e66b38bfefdc8ea61aa223a7079847c2ef7422`.

GitHub Actions:
- Core20 quality gates run 933: SUCCESS;
- Core20 regression: 215 passed;
- results-integrity: SUCCESS.

The first validation run had 214 passed / 1 failed because an older regression still
expected the previous SEMANTIC_PROOF_REQUIRED state for this exact FNP requirement.
The expectation was updated to STRUCTURED_PROOF_REQUIRED; no unrelated regression
failed.

### Frontier

Relative to the historical 35-item semantic frontier from the saved 2026-10-02 run,
four requirements are now deterministic in current code:
- `PP87-12-A1-ZOUIT`;
- `SP4-8.2.3-FIRE-ROAD-WIDTH`;
- `SP4-8.2.6-ROAD-WALL-DISTANCE`;
- `FNP505-1215-CONVEYOR-CROSSING-SPACING`.

Conceptual historical remainder: 31 items.
This is still not a live runtime queue count. Recompute before any semantic AI wave.

Next candidates:
1. `FZ384-4-1-ID-FEATURES` — owner-scoped set completeness is promising because
   the statutory identification features are an explicit finite list;
2. `SP18-5.37-ENTRANCE-GATE-WIDTH` — requires a relative-formula contract
   (vehicle width + 1.5 m plus absolute minimum);
3. keep `GOST27751-10.1-CLASS-LEVEL-GAMMA` held until the gamma=1.2 special-case
   override is explicitly modeled.


## Deterministic normative proof expansion — 384-FZ identification features — 2026-10-06

### Goal

Replace semantic AI review of the finite statutory identification-feature list with
a fail-closed owner-scoped deterministic completeness proof.

### Set-engine refinement

SET_COMPLETENESS now supports two optional disclosure controls:
- `allow_negated_evidence` — only for requirements where an explicit negative
  value is still a valid disclosed value (for example, "не относится к ОПО");
- `assertion_regexes` — lexical presence alone is insufficient; an element must
  also be expressed as a local project assertion.

For elements with assertion_regexes, the broad generic applicability-negation window
no longer overrides the local assertion. This prevents an unrelated phrase such as
"не относится к ОПО" from falsely negating neighboring identification fields on the
same page.

Core commits:
- `74d50e37cb5a2e9e90440a6d970fffdc3f7adbac`;
- `85134acb6a7107abd501362c5db713943b02901e`.

### FZ384-4-1-ID-FEATURES

Converted from semantic proof to owner-scoped SET_COMPLETENESS with
`DETERMINISTIC_AFTER_COMPLETE`.

Seven required identification features:
1. purpose;
2. functional/technological characteristics;
3. dangerous natural processes / technogenic impacts;
4. belonging to hazardous production facilities (OPO);
5. fire and explosion/fire hazard;
6. permanent occupancy of people;
7. responsibility level.

Owner scope:
- `SAME_CONFIRMED_OBJECT`;
- evidence from different Project Understanding objects is never merged.

Disclosure rules:
- copied statutory enumeration does not prove the project values;
- negative OPO disclosure is accepted when explicitly asserted;
- negative permanent-occupancy disclosure is accepted when explicitly asserted;
- responsibility level requires an actual value: повышенный / нормальный / пониженный.

Registry commits:
- `07fe0c90eaf69a4a1aac9e08d47528b2bd474457`;
- `c96f65bda3a9594c0285c4f57665a4d7b8beaed6`.

Regression commit:
- `646fc62b24ddc9d1ad08149963e0f283b645e86c`.

Coverage:
- complete seven-feature set for one confirmed object -> deterministic VERIFIED_OK;
- copied 384-FZ list -> no promotion;
- one missing feature -> REVIEW_QUESTION;
- split evidence across two objects -> no promotion;
- generic negated set evidence remains rejected unless the element explicitly opts in.

### Validation

Temporary draft PR #10 was used only for validation and closed without merge.

Final functional head:
`c96f65bda3a9594c0285c4f57665a4d7b8beaed6`.

GitHub Actions:
- Core20 quality gates run 942: SUCCESS;
- Core20 regression: 220 passed;
- results-integrity: SUCCESS.

The first validation run had 219 passed / 1 failed. It exposed a pre-existing broad
negation window that could let an OPO negative assertion suppress adjacent
identification fields. The set-engine fix made asserted fields local; the second run
was fully green.

### Frontier

Relative to the historical 35-item semantic frontier from the saved 2026-10-02 run,
five requirements are now deterministic in current code:
- `PP87-12-A1-ZOUIT`;
- `SP4-8.2.3-FIRE-ROAD-WIDTH`;
- `SP4-8.2.6-ROAD-WALL-DISTANCE`;
- `FNP505-1215-CONVEYOR-CROSSING-SPACING`;
- `FZ384-4-1-ID-FEATURES`.

Conceptual historical remainder: 30 items.
This remains a historical count, not a live runtime queue. Do not run semantic AI
before recomputing the saved project against the current registry.

Next candidates:
1. `FZ384-4-11-ID-IN-ASSIGNMENT-PD` — cross-document comparison of the same
   identification-feature set between assignment/input data and PD;
2. `SP18-5.37-ENTRANCE-GATE-WIDTH` — relative formula proof
   (vehicle width + 1.5 m and absolute minimum 3.5 m);
3. keep `GOST27751-10.1-CLASS-LEVEL-GAMMA` held until its special-case
   gamma=1.2 override is modeled.


## Deterministic normative proof expansion — responsibility level in input data — 2026-10-06

### Goal

Remove `FZ384-15-2-RESP-INPUT` from semantic AI review only if the project proves
an actual responsibility level in a real design assignment / input-data source.

### Source-scoped set evidence

SET_COMPLETENESS now supports optional `source_aliases`.

Important contract:
- source aliases are matched only against document metadata
  (`document`, `document_type`, `section`);
- a PD page that merely says "в задании на проектирование..." cannot satisfy a
  source-scoped input-data requirement;
- the source constraint is independent from the textual assertion inside the page.

Core commit:
- `f3071ff4d65501f54793d73e80213b75a2177299`.

### FZ384-15-2-RESP-INPUT

Converted from semantic proof to one-element owner-scoped SET_COMPLETENESS.

Required proof:
1. source metadata identifies a design assignment / input-data document;
2. the same confirmed Project Understanding owner is attached to that page;
3. the page explicitly states "уровень ответственности";
4. one statutory value is present: повышенный / нормальный / пониженный.

Promotion:
- `DETERMINISTIC_AFTER_COMPLETE`;
- no semantic Judge/Critic is needed after complete proof;
- absence or weak evidence remains fail-closed review, never PROJECT_FINDING.

Registry commits:
- `bb6fb114b0527f820be97a4679319f947a675c87`;
- `557ec9c746de41bd56a0efd92c953d3763dbcc2a`;
- `f4fa3115e0fb3905dde6977e4b83abfe10b723ae`.

Regression commit:
- `5a13f11d507521b1dcbbcf19ede936d58ebaf060`.

Coverage:
- explicit level in actual assignment -> deterministic VERIFIED_OK;
- identical text in PD -> does not satisfy the source requirement;
- assignment without an actual level value -> no promotion;
- textual reference to an assignment does not override document metadata.

### Evidence Quality issue exposed by validation

The first runs showed `NORMATIVE_POSITIVE_EVIDENCE_NOT_FOUND` even for
"Уровень ответственности объекта: нормальный." in a confirmed assignment.

Cause:
- Evidence Quality 10.1.2 uses the first two discriminative stems of `topic`;
- the old topic "Исходные данные и уровень ответственности" made "исходные"
  a mandatory body-text topic anchor;
- this duplicated the newly explicit source-scope contract and rejected legitimate
  assignment pages whose body did not repeat the document type.

Fix:
- topic reordered to "Уровень ответственности в исходных данных";
- content alignment now checks the engineering concept first;
- source identity remains strictly enforced by `source_aliases`;
- no global quality threshold was weakened.

Diagnostic-only commits used to isolate the pipeline:
- `f1aad380f031e6a53b87aa21907561a3d5d1ced6`;
- `381d5006155ece89bdd1ae683e7c91cf5d903510`;
- `cf1c4328e8dd7bfb56d006114e0096937349dcb5`.

### Validation

Temporary draft PR #11 was used only for validation and closed without merge.

Final functional head:
`f4fa3115e0fb3905dde6977e4b83abfe10b723ae`.

GitHub Actions:
- Core20 quality gates run 956: SUCCESS;
- Core20 regression: 224 passed;
- results-integrity: SUCCESS.

### Frontier

Relative to the historical 35-item semantic frontier from the saved 2026-10-02 run,
six requirements are now deterministic in current code:
- `PP87-12-A1-ZOUIT`;
- `SP4-8.2.3-FIRE-ROAD-WIDTH`;
- `SP4-8.2.6-ROAD-WALL-DISTANCE`;
- `FNP505-1215-CONVEYOR-CROSSING-SPACING`;
- `FZ384-4-1-ID-FEATURES`;
- `FZ384-15-2-RESP-INPUT`.

Conceptual historical remainder: 29 items.
This is still not a live runtime queue count.

### Held requirement

`FZ384-4-11-ID-IN-ASSIGNMENT-PD` remains intentionally held.
Presence of identification fields in both assignment and PD is insufficient:
a safe deterministic proof must compare the actual values of the same features
across both sources and fail closed on disagreement.

Next candidates:
1. `SP18-5.37-ENTRANCE-GATE-WIDTH` — relative formula proof
   (vehicle width + 1.5 m plus absolute minimum 3.5 m);
2. `FZ384-4-11-ID-IN-ASSIGNMENT-PD` only after a reusable cross-document
   value-consistency contract exists;
3. `GOST27751-10.1-CLASS-LEVEL-GAMMA` remains held until its gamma=1.2
   special-case applicability is modeled.


## Deterministic normative proof expansion — PP87 insolation and daylight results — 2026-10-06

### Goal

Remove `PP87-13-D1-INSOLATION` from semantic AI review only when both calculation
results required by the verified atomic clause are addressably present.

### Contract

`PP87-13-D1-INSOLATION` now uses deterministic SET_COMPLETENESS with two required
elements:
1. numeric result for duration of insolation;
2. numeric result for daylight factor / КЕО.

Each element requires a local assertion tying the engineering label to a numeric
value. A heading or copied PP87 clause without actual results does not satisfy the
set.

Promotion:
- `DETERMINISTIC_AFTER_COMPLETE`;
- both elements are required;
- no PROJECT_FINDING is inferred from absence;
- incomplete evidence remains specialist review.

Registry commits:
- `0286d6c76ca8a1a8bc2f67090ff2526e8b9fb61a`;
- `af5a56d04fd4c6f29ce76427960fd9149ab0b22f`.

Regression commit:
- `62d2adab37924c639fbd2f924a86620eeac583db`.

Coverage:
- numeric insolation + numeric KEO, including on separate AR pages -> deterministic
  VERIFIED_OK;
- heading / descriptive statement without numeric results -> no promotion;
- only one of the two results -> REVIEW_QUESTION;
- copied requirement containing clause numbering -> no promotion.

### Retrieval / proof separation exposed by validation

The first validation run had 226 passed / 2 failed because Evidence Quality 10.1.2
treated the combined topic "Инсоляция и КЕО" as if both topic anchors had to occur
on each individual page. That conflicts with a multi-page completeness proof.

The fix is contract-local:
- retrieval topic is now `Инсоляция`;
- retrieval threshold is one concept hit;
- final proof remains strict and still requires both numeric set elements.

Therefore retrieval is allowed to route one valid evidence page into the proof
engine, while SET_COMPLETENESS — not retrieval — decides whether the complete
two-result obligation is satisfied. No global quality threshold was weakened.

### Validation

Temporary draft PR #12 was used only for validation and closed without merge.

Final functional head:
`af5a56d04fd4c6f29ce76427960fd9149ab0b22f`.

GitHub Actions:
- Core20 quality gates run 962: SUCCESS;
- Core20 regression: 228 passed;
- results-integrity: SUCCESS.

### Frontier and held contracts

Relative to the historical 35-item semantic frontier from the saved 2026-10-02 run,
seven requirements are now deterministic in the current codebase:
- `PP87-12-A1-ZOUIT`;
- `SP4-8.2.3-FIRE-ROAD-WIDTH`;
- `SP4-8.2.6-ROAD-WALL-DISTANCE`;
- `FNP505-1215-CONVEYOR-CROSSING-SPACING`;
- `FZ384-4-1-ID-FEATURES`;
- `FZ384-15-2-RESP-INPUT`;
- `PP87-13-D1-INSOLATION`.

Conceptual historical remainder: 28 items.
This remains a historical frontier, not a live queue count.

`SP18-5.37-ENTRANCE-GATE-WIDTH` is intentionally held because the current atomic
record combines two applicability branches:
- automobile entrance: max vehicle width + 1.5 m, but not less than 3.5 m;
- railway entrance: not less than 4.5 m.
Promoting the whole record from only the automobile formula could hide an applicable
railway entrance. Split atomization or a proven entrance-type applicability inventory
is required before deterministic promotion.

`FZ384-4-11-ID-IN-ASSIGNMENT-PD` also remains held until a cross-document
value-consistency proof compares actual identification-feature values, not mere
presence in both sources.

Do not run another semantic AI wave before recomputing the saved project against
the current registry.


## Deterministic normative proof expansion — closed storm sewer — 2026-10-06

### Goal

Remove `SP18-5.52-CLOSED-STORM-SEWER` from semantic review only when project
evidence explicitly proves that the storm-water sewer itself is closed / of closed
type.

### Contract

`SP18-5.52-CLOSED-STORM-SEWER` now uses deterministic SET_COMPLETENESS with one
strict element:
- storm-water / rainwater sewer;
- locally tied to `закрытая` / `закрытого типа`.

Accepted lexical families:
- дождевая канализация;
- ливневая канализация.

The closed-type assertion is sentence-local. A nearby unrelated phrase such as
"закрытая система хозяйственно-бытовой канализации" cannot be combined with
"дождевая канализация открытая" to create a false proof.

Promotion:
- `DETERMINISTIC_AFTER_COMPLETE`;
- generic mention of storm-water drainage without closed type does not promote;
- absence remains REVIEW_QUESTION, never PROJECT_FINDING.

Registry commits:
- `4db403614ff846f357c714ecd01ffcea213ed8eb`;
- `b78d36cb107ba6ee22c6ae6a62a854bea399014d`.

Regression commit:
- `c40dfdd2658f98b0dead3206aeeb1984cd4763cc`.

Coverage:
- "Система дождевой канализации принята закрытого типа" -> deterministic VERIFIED_OK;
- equivalent "ливневая канализация ... закрытого типа" -> deterministic VERIFIED_OK;
- generic storm sewer without closed-type assertion -> no promotion;
- unrelated closed sanitary sewer + open storm sewer -> no promotion.

### Retrieval / proof separation

The retrieval topic is intentionally broad (`Канализация`) with a one-hit retrieval
threshold. Retrieval may route relevant sewer pages, but only the strict local
SET_COMPLETENESS assertion can create VERIFIED_OK. This avoids coupling the quality
gate to one vocabulary variant while keeping the proof fail-closed.

### Validation

Temporary draft PR #13 was used only for validation and closed without merge.

Final functional head:
`c40dfdd2658f98b0dead3206aeeb1984cd4763cc`.

GitHub Actions:
- Core20 quality gates run 967: SUCCESS;
- Core20 regression: 232 passed;
- results-integrity: SUCCESS.

### Frontier

Relative to the historical 35-item semantic frontier from the saved 2026-10-02 run,
eight requirements are now deterministic in the current expansion line.

Conceptual historical remainder: 27 items.
This remains a historical count, not a live runtime queue.


## Hybrid deterministic set fast path with semantic fallback — 2026-10-06

### Goal

Allow complex normative clauses to use a strict deterministic sufficient-condition
proof without sacrificing semantic coverage for other valid formulations.

### New promotion policy

SET_COMPLETENESS now supports:
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Behavior:
- complete strict set -> deterministic VERIFIED_OK;
- incomplete strict set with addressable retrieval evidence -> REVIEW_QUESTION with
  `SEMANTIC_PROOF_REQUIRED`, therefore the requirement stays in the semantic queue;
- no negative conclusion is inferred from an incomplete deterministic fast path.

This is intentionally different from:
- `DETERMINISTIC_AFTER_COMPLETE`: incomplete set remains a set-proof review;
- `SEMANTIC_AFTER_COMPLETE`: even a complete set still requires semantic proof.

Core commit:
- `97d38b7ae4ae171b1954f5f0f4e8300f83a4d6af`.

Regression commit:
- `170a8672b3ea8625b13f9fd75fe6202039864ea8`.

Regression coverage:
- complete hybrid set -> deterministic proof, semantic queue total = 0;
- incomplete hybrid set -> semantic fallback, semantic queue total = 1;
- fallback never creates PROJECT_FINDING.

### Validation

Temporary draft PR #14 was used only for validation and closed without merge.

Final functional head:
`170a8672b3ea8625b13f9fd75fe6202039864ea8`.

GitHub Actions:
- Core20 quality gates run 971: SUCCESS;
- Core20 regression: 234 passed;
- results-integrity: SUCCESS.

This checkpoint changes proof routing only; no normative requirement was converted by
this step itself.


## Hybrid deterministic fast path — FNP505 surface emergency lighting — 2026-10-06

### Goal

Accelerate `FNP505-1461-SURFACE-EMERGENCY-LIGHTING` without replacing semantic
coverage with a narrower deterministic interpretation.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Deterministic fast path is deliberately conservative. It requires one addressable
universal assertion tying together:
- all / each objects of the surface complex;
- emergency lighting;
- an independent power source.

A statement limited only to "each workplace" is not enough for the fast path,
because the clause separately covers listed technological and auxiliary buildings.
Such evidence is preserved for semantic proof instead of being rejected or
incorrectly promoted.

Likewise, an assertion that mentions emergency lighting but does not establish an
independent power source cannot produce VERIFIED_OK.

Registry commit:
- `1ab7727956d1b2525a4c67032967066d35de97c5`.

Regression commit:
- `251a3a7b4444422e8992201c26dc4bcae44bbe9e`.

Coverage:
- universal surface-complex coverage + emergency lighting + independent source ->
  deterministic VERIFIED_OK;
- workplace-only formulation -> semantic fallback;
- universal scope without independent source -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #15 was used only for validation and closed without merge.

Final functional head:
`251a3a7b4444422e8992201c26dc4bcae44bbe9e`.

GitHub Actions:
- Core20 quality gates run 975: SUCCESS;
- Core20 regression: 237 passed;
- results-integrity: SUCCESS.

### Frontier semantics

This requirement is now hybrid rather than fully deterministic:
- qualifying evidence bypasses AI;
- non-qualifying but addressable evidence still remains in the semantic queue.

Therefore this change reduces AI work opportunistically but does not decrement the
historical semantic frontier count by itself.


## Hybrid deterministic fast path — PP87 transport communications — 2026-10-06

### Goal

Accelerate `PP87-12-I-TRANSPORT` for production projects when the PZU contains an
explicit project assertion that the transport-communications scheme is justified for
both external and internal freight traffic.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Deterministic fast path requires one local assertion containing:
- the transport-communications scheme;
- external freight traffic;
- internal freight traffic;
- an explicit project-level justification statement.

The assertion regex deliberately requires a project statement with the scheme before
the justification phrase. A copied normative sentence of the form
"схемы ... должны быть обоснованы" does not satisfy the fast path.

Applicability routing remains unchanged and still depends on the production-project
profile.

Registry commit:
- `9af8fd0a0e27e6d3c9fc2e6135dad032109d4d6b`.

Regression commit:
- `0cb14a6cfb3c7cfd88b62d5bdfbcca55d9c9ca9a`.

Coverage:
- explicit justified scheme for external + internal freight -> deterministic VERIFIED_OK;
- copied PP87 wording -> semantic fallback;
- external-only scheme -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #16 was used only for validation and closed without merge.

Final functional head:
`0cb14a6cfb3c7cfd88b62d5bdfbcca55d9c9ca9a`.

GitHub Actions:
- Core20 quality gates run 979: SUCCESS;
- Core20 regression: 240 passed;
- results-integrity: SUCCESS.

### Frontier semantics

This requirement is hybrid:
- qualifying evidence bypasses AI;
- other addressable evidence remains available to semantic proof.

Therefore the historical semantic frontier count is unchanged by this step alone.


## Hybrid deterministic fast path — PP87 zoning — 2026-10-06

### Goal

Accelerate `PP87-12-H-ZONING` for production projects without replacing semantic
review for incomplete or differently worded evidence.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Deterministic fast path requires two independently asserted elements:
1. zoning of the territory is explicitly justified;
2. the principal scheme for placement of territorial zones is explicitly justified.

Both assertions must be project statements. A copied PP87 formulation such as
"должно быть обосновано зонирование..." does not satisfy the fast path.

Applicability remains profile-based for production projects.

The retrieval topic was narrowed from "Зонирование производственной территории" to
"Зонирование территории" so the project profile proves production applicability
while the evidence-quality gate focuses on the engineering subject itself.

Registry commit:
- `5abfb567a6ab9b64615ce97e3a80cdc70fa9d740`.

Regression commits:
- `1486de7971e0145068cd7afcdcf9ba79eda771ff`;
- `431dcc4f4276704188c3429673a6fb24a77fe953`.

The second regression commit updates an older test that intentionally expected the
same zoning requirement to remain semantic. It still remains semantic when the fast
path is incomplete, but now the proof type is SET_COMPLETENESS and the fallback state
is `SEMANTIC_PROOF_REQUIRED`.

Coverage:
- both zoning justification and zone-scheme justification -> deterministic VERIFIED_OK;
- copied normative wording -> semantic fallback;
- zoning justified but scheme merely shown -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #17 was used only for validation and closed without merge.

Final functional head:
`431dcc4f4276704188c3429673a6fb24a77fe953`.

GitHub Actions:
- Core20 quality gates run 985: SUCCESS;
- Core20 regression: 243 passed;
- results-integrity: SUCCESS.

### Frontier semantics

This requirement is hybrid:
- qualifying evidence bypasses AI;
- incomplete/differently phrased evidence remains semantic.

Therefore the historical semantic frontier count is unchanged by this hybrid step.


## Hybrid deterministic fast path — PP87 landscaping description — 2026-10-06

### Goal

Accelerate `PP87-12-G-LANDSCAPE` without expanding the verified atomic clause
beyond the registry wording "описаны решения по благоустройству территории".

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Deterministic fast path requires an explicit project statement in which
landscaping / site-improvement solutions are actually described or adopted, for
example through verbs such as:
- предусматривают / предусмотрено;
- приняты;
- выполняются;
- включают.

The fast path intentionally does NOT require specific landscaping subcomponents
such as greening, external lighting, or small architectural forms because those
items are not present in the current verified atomic registry clause.

A copied normative sentence ("должны быть описаны решения...") or a heading-only
mention cannot produce VERIFIED_OK and remains available to semantic proof.

Registry commit:
- `7b1f8f8969a326371a27bc382960e379a06d365c`.

Regression commit:
- `9bc89e449470991b91cef18f20233a30055bcb8d`.

Coverage:
- explicit project landscaping solution -> deterministic VERIFIED_OK;
- copied PP87 obligation -> semantic fallback;
- heading/reference without an actual solution description -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #18 was used only for validation and closed without merge.

Final functional head:
`9bc89e449470991b91cef18f20233a30055bcb8d`.

GitHub Actions:
- Core20 quality gates run 989: SUCCESS;
- Core20 regression: 246 passed;
- results-integrity: SUCCESS.

### Frontier semantics

This requirement is hybrid:
- qualifying project wording bypasses AI;
- other addressable evidence remains semantic.

Therefore the historical semantic frontier count is unchanged by this hybrid step.


## Hybrid deterministic fast path — PP87 planning organization — 2026-10-06

### Goal

Accelerate `PP87-12-C-PLANNING` while preserving the verified clause exactly:
the PZU must contain both a description and a justification of planning-organization
solutions for the land plot.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Two independent elements are required for the deterministic fast path:
1. an actual project description / adopted planning-organization solution;
2. an explicit justification of that solution.

A copied regulatory obligation ("должны быть обоснованы и описаны...") does not
satisfy either project-assertion contract. A described solution without an explicit
justification also does not produce VERIFIED_OK and remains available to semantic proof.

Registry commit:
- `79630cda6fbd9deea874efe2aa7ccaf42bb20e3a`.

Regression commit:
- `f5556113b0ae4a8855159dc382bd8a445be61138`.

Coverage:
- description + justification, including on different PZU pages -> deterministic VERIFIED_OK;
- copied PP87 wording -> semantic fallback;
- description without justification -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #19 was used only for validation and closed without merge.

Final functional head:
`f5556113b0ae4a8855159dc382bd8a445be61138`.

GitHub Actions:
- Core20 quality gates run 993: SUCCESS;
- Core20 regression: 249 passed;
- results-integrity: SUCCESS.

### Frontier semantics

This requirement is hybrid:
- qualifying evidence bypasses AI;
- incomplete/differently phrased evidence remains semantic.

The historical semantic frontier count is unchanged by this hybrid step.


## Hybrid deterministic fast path — PP87 natural lighting — 2026-10-06

### Goal

Accelerate `PP87-13-E-LIGHT` without expanding the verified atomic clause:
the AR must describe architectural solutions providing natural lighting for rooms
with permanent occupancy.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

The deterministic fast path requires one explicit project assertion linking:
- rooms / premises with permanent occupancy;
- a project action/solution such as "обеспечиваются", "предусматривается" or "принято";
- natural lighting.

A copied PP87 obligation does not satisfy the assertion contract. A generic statement
that natural lighting exists, without tying it to rooms with permanent occupancy,
also cannot produce VERIFIED_OK.

Registry commit:
- `db9442c0ed6747de4abcd440be45285d9036a694`.

Regression commit:
- `0d9e79f73f9c07cf784ff9db885081ce84daf098`.

Coverage:
- explicit natural-light solution for permanent-occupancy rooms -> deterministic VERIFIED_OK;
- copied PP87 wording -> semantic fallback;
- natural lighting without the permanent-occupancy relation -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #20 was used only for validation and closed without merge.

Final functional head:
`0d9e79f73f9c07cf784ff9db885081ce84daf098`.

GitHub Actions:
- Core20 quality gates run 997: SUCCESS;
- Core20 regression: 252 passed;
- results-integrity: SUCCESS.

### Frontier semantics

This requirement is hybrid:
- qualifying evidence bypasses AI;
- incomplete/differently phrased evidence remains semantic.

The historical semantic frontier count is unchanged by this hybrid step.


## Hybrid deterministic fast path — PP87 sanitary planning — 2026-10-06

### Goal

Accelerate `PP87-13-H-SANITARY` while preserving the verified atomic clause:
AR must describe and justify volume-planning solutions that ensure compliance with
sanitary-epidemiological requirements.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Two independent elements are required:
1. an explicit project assertion that the volume-planning solutions ensure
   sanitary-epidemiological requirements;
2. an explicit justification of those volume-planning solutions.

The fast path does not infer justification from the compliance statement itself.
A copied regulatory obligation also does not satisfy the project-assertion contract.

Registry commit:
- `2eb61d2150fefdb7f9b4e51658ebaff50a4a72c2`.

Regression commit:
- `84f2e50159172a87d713e77a673ad01071773e78`.

Coverage:
- compliance assertion + separate justification -> deterministic VERIFIED_OK;
- copied PP87 wording -> semantic fallback;
- compliance assertion without justification -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #21 was used only for validation and closed without merge.

Final functional head:
`84f2e50159172a87d713e77a673ad01071773e78`.

GitHub Actions:
- Core20 quality gates run 1001: SUCCESS;
- Core20 regression: 255 passed;
- results-integrity: SUCCESS.

### Frontier semantics

This requirement is hybrid:
- qualifying evidence bypasses AI;
- incomplete/differently phrased evidence remains semantic.

The historical semantic frontier count is unchanged by this hybrid step.


## Hybrid deterministic fast path — PP87 facade and interior composition — 2026-10-06

### Goal

Accelerate `PP87-13-C-FACADE` without narrowing the verified clause:
AR must describe and justify composition techniques for both facades and interiors.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Two independent deterministic elements are required:
1. an explicit project description/adoption of composition techniques covering both
   facades and interiors;
2. an explicit justification covering the same two domains.

The fast path deliberately requires both facade and interior scope. A facade-only
statement cannot close the requirement. A copied PP87 obligation also cannot satisfy
the project-assertion contract.

Registry commit:
- `bbf3cc16b7f94187bcfa67b65602d7a1f5098e14`.

Regression commit:
- `8e3ce8cc63e733c1dcd116fcf50348848111c18f`.

Coverage:
- project description + justification for facades and interiors -> deterministic VERIFIED_OK;
- copied PP87 wording -> semantic fallback;
- facade-only composition statement -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #22 was used only for validation and closed without merge.

Final functional head:
`8e3ce8cc63e733c1dcd116fcf50348848111c18f`.

GitHub Actions:
- Core20 quality gates run 1005: SUCCESS;
- Core20 regression: 258 passed;
- results-integrity: SUCCESS.

### Frontier semantics

This requirement is hybrid:
- qualifying evidence bypasses AI;
- incomplete/differently phrased evidence remains semantic.

The historical semantic frontier count is unchanged by this hybrid step.


## Hybrid deterministic fast path — PP87 room finishing — 2026-10-06

### Goal

Accelerate `PP87-13-D-FINISH` while preserving the verified atomic clause:
AR must describe and justify finishing solutions for rooms of primary, auxiliary,
service and technical purpose.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Two independent elements are required:
1. an explicit project description/adoption of finishing solutions covering all four
   room-purpose groups;
2. an explicit justification covering the same scope.

The fast path deliberately requires all four groups. A partial statement for only
primary and auxiliary rooms cannot close the requirement. A copied PP87 obligation
also cannot satisfy the project-assertion contract.

Registry commit:
- `d7f16425aee09b14318469d3f25932a89881d76c`.

Regression commit:
- `251fb578b6833082fc02a325b8847ea99627466a`.

Coverage:
- all four groups + project solution + separate justification -> deterministic VERIFIED_OK;
- copied PP87 wording -> semantic fallback;
- partial room-purpose scope -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #23 was used only for validation and closed without merge.

Final functional head:
`251fb578b6833082fc02a325b8847ea99627466a`.

GitHub Actions:
- Core20 quality gates run 1009: SUCCESS;
- Core20 regression: 261 passed;
- results-integrity: SUCCESS.

### Frontier semantics

This requirement is hybrid:
- qualifying evidence bypasses AI;
- incomplete/differently phrased evidence remains semantic.

The historical semantic frontier count is unchanged by this hybrid step.


## Hybrid deterministic fast path — PP87 engineering preparation and protection — 2026-10-06

### Goal

Accelerate `PP87-12-E-ENGINEERING-PREP` while preserving the verified atomic clause:
PZU must describe and justify solutions for engineering preparation and engineering
protection of the territory from hazardous processes and water impacts.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Two independent elements are required:
1. an explicit project description/adoption of engineering-preparation and
   engineering-protection solutions, tied to hazardous processes / surface and
   groundwater impacts;
2. an explicit justification of the same solution scope.

A statement only about engineering preparation, without engineering protection, does
not satisfy the fast path. A copied PP87 obligation also remains semantic.

Registry commit:
- `877d51e5e7b5ecfa8d441c9e24aa5d710f678829`.

Regression commits:
- `1a64b7a381449c9c06ced6d2587e6026ca6fe0b8`;
- `2b42e68fdee5638ab59ebd147f0e956558ff0ee5`.

The second regression commit updates an older proof test that intentionally checks
that keyword evidence alone is not normative proof. The scenario still remains
semantic; its proof type is now SET_COMPLETENESS with semantic fallback.

Coverage:
- engineering preparation + protection + hazardous/water scope + separate
  justification -> deterministic VERIFIED_OK;
- copied PP87 wording -> semantic fallback;
- preparation without protection scope -> no automatic verification;
- keyword-only legacy case -> remains semantic;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #24 was used only for validation and closed without merge.

Final functional head:
`2b42e68fdee5638ab59ebd147f0e956558ff0ee5`.

GitHub Actions:
- Core20 quality gates run 1015: SUCCESS;
- Core20 regression: 264 passed;
- results-integrity: SUCCESS.

### Frontier semantics

This requirement is hybrid:
- qualifying evidence bypasses AI;
- incomplete/differently phrased evidence remains semantic.

The historical semantic frontier count is unchanged by this hybrid step.


## Hybrid deterministic fast path — SP12 sequential category calculation — 2026-10-06

### Goal

Accelerate `SP12-5.2-SEQUENTIAL-CATEGORY` without replacing semantic review for
shorter or differently documented category calculations.

### Contract

The requirement now uses owner-scoped SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

The deterministic fast path requires one explicit project assertion that:
- the category of a room was actually determined/calculated;
- the determination was performed sequentially;
- the order is explicitly recorded as A -> Б -> В1-В4 -> Г -> Д;
- the evidence belongs to one confirmed Project Understanding owner.

A copied normative instruction ("должно выполняться...") does not satisfy the
project-assertion contract. An incomplete order also cannot produce VERIFIED_OK.

Registry commit:
- `f3c5dba416bbf7a27827e48c2f47b4364c62c2ae`.

Regression commit:
- `2e886a50ab612d32e859446e4618cba2650c2a66`.

Coverage:
- full explicit sequence for one confirmed room/object -> deterministic VERIFIED_OK;
- copied SP12 requirement -> semantic fallback;
- incomplete sequence -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #25 was used only for validation and closed without merge.

Final functional head:
`2e886a50ab612d32e859446e4618cba2650c2a66`.

GitHub Actions:
- Core20 quality gates run 1019: SUCCESS;
- Core20 regression: 267 passed;
- results-integrity: SUCCESS.

### Held related contracts

`GOST27751-10.2-ASSIGNMENT` remains held because it depends on the minimum values
and special cases of p. 10.1; source presence alone is insufficient.

`SP6-2025-5.2-SPZ-RELIABILITY` remains held because the clause contains the
special-group branch for specific objects. A safe fast path must not silently treat
ordinary I category as sufficient where that branch applies.

### Frontier semantics

This requirement is hybrid:
- qualifying evidence bypasses AI;
- incomplete/differently phrased evidence remains semantic.

The historical semantic frontier count is unchanged by this hybrid step.


## Historical semantic frontier reclassification against current registry — 2026-10-06

### Why this replaces the old conceptual remainder counter

The saved 2026-10-02 project run contains 43 requirement IDs in its historical
semantic-pending rows. That queue is stale relative to the current registry: several
IDs that were semantic at run time now have deterministic or hybrid proof contracts.

Therefore the earlier hand-maintained "35 -> 27" conceptual remainder is no longer
the best control metric.

### Current registry classification of the 43 historical IDs

- deterministic contracts: **15**;
- hybrid deterministic-fast-path / semantic-fallback contracts: **11**;
- still pure semantic / cross-document-unmodeled contracts: **17**.

This classification is based on the current registry contract shape, not on a fresh
runtime execution of the project documents.

Deterministic examples include:
- typed proofs for FNP505-1215 and SP4 8.2.3 / 8.2.6;
- owner-scoped set proofs for FZ123-27-3, FZ384-4-1, FZ384-15-2, SP12-4.2,
  SP52-7.6.1 and SP6-5.3;
- deterministic presence / completeness contracts such as ZOUIT, responsibility
  level, transport parameters, insolation/KEO and closed storm sewer.

Hybrid examples include:
- PP87 planning, engineering preparation, landscaping, zoning, transport,
  facade/interior, room finishing, natural lighting and sanitary planning;
- FNP505 surface-complex emergency lighting;
- SP12 sequential category calculation.

Pure-semantic / held examples include:
- FZ384-4-11 cross-document identification-value consistency;
- GOST27751 10.1 / 10.2;
- SP18 5.37 entrance-gate formula with automobile/rail applicability branches;
- SP6 5.2 special-group reliability branch;
- remaining fire-safety, energy-efficiency and descriptive PP87 clauses.

### Control rule

Do not use the old conceptual remainder count as a live queue.
For development prioritization use the current-registry split **15 deterministic /
11 hybrid / 17 semantic**.
A true runtime queue must still be recomputed from the project documents before a
new semantic AI wave.


## Hybrid deterministic fast path — PP87 architectural justification — 2026-10-06

### Goal

Accelerate `PP87-13-B-ARCH` while preserving the verified atomic clause:
AR must justify both adopted volume-spatial and architectural-artistic solutions.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Two independent elements are required:
1. explicit justification of adopted volume-spatial solutions;
2. explicit justification of adopted architectural-artistic solutions.

The fast path does not infer one domain from the other. A copied PP87 obligation
also does not satisfy the project-assertion contract.

Registry commit:
- `ac206b1817e223a03055ed3938b72848c23f8c68`.

Regression commit:
- `f14a8f6eda44d6886c2af3b30bbf5e00b8b9528c`.

Coverage:
- both justifications -> deterministic VERIFIED_OK;
- copied PP87 wording -> semantic fallback;
- one domain only -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #26 was used only for validation and closed without merge.

Final functional head:
`f14a8f6eda44d6886c2af3b30bbf5e00b8b9528c`.

GitHub Actions:
- Core20 quality gates run 1024: SUCCESS;
- Core20 regression: 270 passed;
- results-integrity: SUCCESS.

### Registry frontier update

Against the 43 IDs from the saved historical semantic queue, the current registry is
now classified as:
- deterministic: 15;
- hybrid: 12;
- pure semantic / unmodeled cross-document: 16.

This is a registry-state classification, not a fresh project runtime queue.


## Hybrid deterministic fast path — SP4 two-sided fire access — 2026-10-06

### Goal

Accelerate `SP4-8.2.1-FIRE-ACCESS-SIDES` without attempting to encode all width
and courtyard applicability branches.

### Safe sufficient condition

The requirement now uses owner-scoped SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

The deterministic fast path is intentionally narrower than the full clause. It
requires an explicit project assertion that:
- fire apparatus / fire equipment access is provided;
- the access runs along the length of the building;
- it is provided from two sides;
- the evidence belongs to one confirmed Project Understanding owner.

This is a sufficient condition independent of the one-sided <=18 m branch and is
also compatible with the two-sided requirement for closed / semi-closed courtyards.

One-sided access is never auto-promoted by this fast path because it requires
additional proof of building width and courtyard type.

### Copied-norm protection

The first validation run exposed a false positive:
"должен быть обеспечен подъезд ... с двух сторон" matched the initial lexical
pattern even though it was only normative obligation wording.

The contract was tightened so the project assertion must be attached to the actual
solution, for example:
"Подъезд пожарной техники по длине здания обеспечен с двух сторон."

Registry commits:
- `bd0de53197ca53ef675ba15df28d5c7d2fb80243`;
- `af433e265d396c6f3c270a267f469a2c259ecff7`.

Regression commit:
- `1cf75e8030b80b8aca2becc7d1c9573460b057fb`.

Coverage:
- explicit two-sided full-length fire access -> deterministic VERIFIED_OK;
- one-sided access -> semantic fallback;
- copied SP4 obligation -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #27 was used only for validation and closed without merge.

Final functional head:
`af433e265d396c6f3c270a267f469a2c259ecff7`.

GitHub Actions:
- Core20 quality gates run 1030: SUCCESS;
- Core20 regression: 273 passed;
- results-integrity: SUCCESS.

### Registry frontier update

Against the 43 IDs from the saved historical semantic queue:
- deterministic: 15;
- hybrid: 13;
- pure semantic / unmodeled cross-document: 15.

This remains a registry-state classification, not a fresh project runtime queue.


## Hybrid deterministic fast path — PP87 land-plot TEP — 2026-10-06

### Goal

Accelerate `PP87-12-D-TEP` without inventing a normative exhaustive list of
technical-economic indicators that is not present in the verified atomic clause.

### Safe sufficient condition

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

The deterministic fast path requires:
1. an explicit block / heading for technical-economic indicators of the land plot;
2. a named numeric land-plot area indicator;
3. a named numeric development coefficient / development-density coefficient.

This is intentionally a sufficient, not exhaustive, proof. Other valid TEP
combinations remain available to semantic proof.

The routing topic was normalized from the abbreviation-only
"ТЭП земельного участка" to the full project wording
"Технико-экономические показатели земельного участка", and the exact keyword
"площадь земельного участка" was added. This prevents Evidence Quality from
rejecting legitimate project pages that do not repeat the abbreviation "ТЭП".

Registry commits:
- `04dd2cafd77c5ab969f54f48dc8e8a9ca342d97a`;
- `3ff4239afc286f04f34cc42ab8b3a416a1087a78`.

Regression commits:
- `5abd09cdf64698617ff4e25bb33934cae701cc0b`;
- `6ec73a57146020ee8ba7b9ae1d83f2b536785fb6`;
- `65b970c2ea2aa57b38dbf49d1a1860f32edfd660`.

Coverage:
- explicit TEP block + numeric site area + numeric development coefficient ->
  deterministic VERIFIED_OK;
- copied PP87 obligation -> semantic fallback;
- incomplete numeric block -> no automatic verification;
- legacy near-miss diagnostics remain valid;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #28 was used only for validation and closed without merge.

Final functional head:
`65b970c2ea2aa57b38dbf49d1a1860f32edfd660`.

GitHub Actions:
- Core20 quality gates run 1040: SUCCESS;
- Core20 regression: 276 passed;
- results-integrity: SUCCESS.

### Registry frontier update

Against the 43 IDs from the saved historical semantic queue:
- deterministic: 15;
- hybrid: 14;
- pure semantic / unmodeled cross-document: 14.

This remains a registry-state classification, not a fresh project runtime queue.


## Hybrid deterministic fast path — PP87 architectural energy-efficiency solutions — 2026-10-06

### Goal

Accelerate `PP87-13-B3-EFF-DESIGN` while preserving the verified atomic clause:
AR must contain both a description and justification of architectural solutions
aimed at improving the energy efficiency of the object.

### Contract

The requirement uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

Two independent elements are required:
1. an explicit project description/adoption of architectural solutions directed at
   improving energy efficiency;
2. an explicit justification of those solutions.

The deterministic fast path does not treat a copied PP87 obligation as project
evidence and does not infer justification from a description alone.

Functional head before this documentation checkpoint:
- `739323d3af2a8304765f53c3fe71e8482266d96b`.

Coverage:
- explicit energy-efficiency architectural solution + separate justification ->
  deterministic VERIFIED_OK;
- copied PP87 wording -> semantic fallback;
- description without justification -> no automatic verification;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #29 was used for validation and closed without merge.

GitHub Actions:
- Core20 quality gates run 1044: SUCCESS;
- Core20 regression: 279 passed;
- results-integrity: SUCCESS.

PR #30 was created after a chat interruption against the same head and closed
without merge as a duplicate validation PR.

### Registry frontier update

Against the 43 IDs from the saved historical semantic queue:
- deterministic: 15;
- hybrid: 15;
- pure semantic / unmodeled cross-document: 13.

This remains a registry-state classification, not a fresh project runtime queue.
## Hybrid deterministic fast path — PP87 energy-efficiency compliance justification — 2026-10-06

### Goal

Accelerate `PP87-13-B1-EFF` while preserving the verified conditional clause:
for objects subject to energy-efficiency requirements, AR must contain a justification
that the adopted architectural solutions comply with those requirements.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

The deterministic fast path is intentionally narrow. It requires an explicit project
justification in which compliance of the architectural solutions with energy-efficiency
requirements is tied to a concrete adopted measure or engineering effect.

Generic statements such as "Приведено обоснование соответствия..." do not prove the
content of the justification and remain semantic. Copied PP87 obligation wording also
does not satisfy the fast path.

Registry commit:
- `ee2cdd62ea8cdd14ab0b512ca539364fbe5761f5`.

Regression commits:
- `a77d1237849c6b40f37ee219acdbd03f3663c29e`;
- `c7729047a113f2f186d34cb87902f65466ea421a`.

Coverage:
- explicit compliance justification + concrete measure/effect -> deterministic VERIFIED_OK;
- generic statement that a justification is present -> semantic fallback;
- copied PP87 wording -> semantic fallback;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #31 was used only for validation and closed without merge.

The first validation run 1049 exposed one stale regression expectation:
the old semantic-only reason code changed, correctly, to the hybrid fast-path fallback
reason code. The contract itself behaved as intended.

Final functional head before this documentation checkpoint:
`c7729047a113f2f186d34cb87902f65466ea421a`.

GitHub Actions run 1051:
- Core20 quality gates: SUCCESS;
- Core20 regression: 281 passed;
- results-integrity: SUCCESS (17 passed).

### Registry frontier update

Against the 43 IDs from the saved historical semantic queue:
- deterministic: 15;
- hybrid: 16;
- pure semantic / unmodeled cross-document: 12.

This remains a registry-state classification, not a fresh project runtime queue.
## Hybrid deterministic fast path — PP87 energy-efficiency measures list — 2026-10-06

### Goal

Accelerate `PP87-13-B2-EFF-MEASURES` while preserving the verified conditional clause:
for applicable objects, AR must contain a list of measures for compliance with
energy-efficiency requirements.

### Contract

The requirement now uses SET_COMPLETENESS with
`DETERMINISTIC_WITH_SEMANTIC_FALLBACK`.

The deterministic fast path is deliberately sufficient rather than exhaustive. It
requires an explicit project list of energy-efficiency measures with actual listed
content, not merely a statement that such a list exists.

Accepted fast-path shape includes an explicit list phrase tied to energy efficiency
and at least two concrete list entries. A copied PP87 obligation or a heading / generic
statement without actual items remains semantic.

Registry commit:
- `0ac247ee01158824115de03f10e7bb19a58173b1`.

Regression commit:
- `16b7fdb441b0a18ad8fbcf0ca6c09efa3914d152`.

Coverage:
- explicit measures list with actual items -> deterministic VERIFIED_OK;
- copied PP87 wording -> semantic fallback;
- heading / statement without listed items -> semantic fallback;
- no PROJECT_FINDING is inferred from a failed fast path.

### Validation

Temporary draft PR #32 was used only for validation and closed without merge.

GitHub Actions run 1055:
- Core20 quality gates: SUCCESS;
- Core20 regression: 284 passed;
- results-integrity: SUCCESS (17 passed).

Final functional head before this documentation checkpoint:
`16b7fdb441b0a18ad8fbcf0ca6c09efa3914d152`.

### Registry frontier update

Against the 43 IDs from the saved historical semantic queue:
- deterministic: 15;
- hybrid: 17;
- pure semantic / unmodeled cross-document: 11.

This remains a registry-state classification, not a fresh project runtime queue.
