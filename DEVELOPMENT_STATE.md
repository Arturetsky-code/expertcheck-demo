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
