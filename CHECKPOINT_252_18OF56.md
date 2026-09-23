# ExpertCheck 25.2 — validated local checkpoint 18/56

Date: 2026-09-23
Branch baseline: `codex/expertcheck-25.2-coverage-breakthrough`
Remote baseline at start of local work: `d0ffdd961c04431299694877066af1dac41c2ba1`
Mode: deterministic Test 78, AI off.

## Reproducible benchmark

- Assignment requirements: 56
- `Соответствует заданию`: 17
- Proven deviations: 1
- `Требует проверки`: 38
- Strict categorical coverage: 18/56 = 32.1%

## Validation

- `tests/core25/test_coverage_breakthrough_252.py`: 17/17 passed
- Other Core25 tests available in the local source snapshot: 93/93 passed
- One historical regression scenario could not be executed because the old XLSX fixture `ExpertCheck_Отчёт_ГИПа_15.0A2.xlsx` is absent from the source snapshot. This was not a code failure.

## Main changes in this checkpoint

- System-scope precedence for engineering-system Assignment rows, so an incidental `ДСК` mention does not force object-owner binding.
- Conservative equipment mismatch guard: a brand-only difference is not enough for a categorical deviation without stronger functional/model/quantity evidence.
- Equipment-register evidence is locked to one physical row to avoid borrowing quantity/model attributes from adjacent equipment rows.
- `SITE_LIGHTING_EXECUTOR` for the composite lighting requirement.
- Open-canopy routing includes `КР`; Test 78 contains the direct proof there.
- Engineering obligations containing generic wording about normative documentation are not automatically misclassified as pure normative-compliance checks.
- Additional deterministic executors recovered from the local Test 78 work are part of the local checkpoint.

## Missing-profile-section rule

This is not a new principle. Existing ExpertCheck logic is fail-closed: absence of a profile section / addressable evidence cannot itself produce either `Соответствует заданию` or a project deviation.

The next Assignment-specific improvement is to expose the reason explicitly, distinguishing:

1. expected profile section is absent from the uploaded package;
2. expected section is present, but evidence admission/proof still failed.

Do not reimplement this as a new verdict gate. Reuse the existing completeness / missing-section infrastructure and wire it into Assignment diagnostics.

## Safety notes from the audit

- Requirement 21 (ore haulage, `SinoTrack` vs `HOWO`) must remain non-categorical on brand difference alone; the found HOWO passage is not enough to prove the same functional role and all required attributes.
- Requirement 22 (loader) remained the single proven equipment deviation at this checkpoint because model identity plus quantity/brand evidence is stronger.
- Lime-supply-system requirement is not a proven deviation merely because ТХ says storage in Big-Bag under a canopy is not provided. Assignment requires delivery in MKR; ТХ separately says lime is delivered in Big-Bags. The 1 m3 container-volume condition still lacks an addressable proof.

## Process rule from this checkpoint forward

After every audited benchmark improvement, create a durable GitHub checkpoint containing at minimum:
- exact baseline/commit SHA;
- benchmark counts;
- tests passed/blocked;
- false-positive audit notes;
- exact code delta (committed code or recovery patch);
- next unfinished task.

Do not rely on chat handoff or ephemeral local filesystem as the only record of validated development progress.
