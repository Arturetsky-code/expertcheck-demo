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
