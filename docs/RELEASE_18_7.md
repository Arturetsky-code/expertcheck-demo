# ExpertCheck 18.7 Candidate · Verification Coverage & Review Compression

## Goal

18.7 targets the bottleneck exposed by the accepted 18.6 control project:

- 347 specialist questions;
- 331 checks outside current automatic coverage;
- 0.6% strict L5 coverage;
- 55.2% evidence coverage L3–L5.

The release does not add a new AI provider or reparse project PDFs. It improves how existing deterministic evidence is closed and how unresolved work is presented to the engineer.

## A. Review Compression

Detailed specialist questions remain fully auditable. The operational queue is rebuilt into cross-object work packages using:

- verification domain;
- stable coverage reason code;
- evidence route;
- checker family;
- engineering topic.

Object identity is no longer part of the package key when the required engineering action is identical. A package may therefore contain homogeneous questions across several objects while preserving every source question ID.

Maximum package size: 40 detailed questions.

Results and reports expose:

- raw specialist-question count;
- work-package count;
- queue compression percentage;
- objects covered by each package;
- stable reason code and recommended action.

## B. Deterministic Agreement Gate

For cross-section status `СОВПАДАЕТ`, L5 may now be reached without a preconfigured owner-section mapping when all of the following are true:

1. at least two physical addressable source records exist;
2. at least two independent trusted sources/section families are confirmed;
3. canonical object_id, parameter_code and unit are complete;
4. engineering binding does not reject the parameter for the object;
5. upstream deterministic comparison already established agreement within tolerance.

Proof kind: `STRUCTURED_AGREEMENT`.

This is a narrower proof route than owner→control and is valid only for agreement.

## C. Structured Conflict preserved in core

18.7 moves the previously runtime-level structured conflict rule into the core:

- two independent trusted addressable sources;
- same canonical object/property/unit;
- different values.

This confirms the fact of conflict as `STRUCTURED_CONFLICT` even if the correct/current value still requires an owner section.

`correct_value_verified=False` unless the owner→control route is also proven.

## D. Restored-project coverage refresh

On a restored Project Knowledge snapshot ExpertCheck recalculates only:

- cross-section deterministic qualification;
- project_review_plan;
- coverage summary.

No source PDF is reread and no AI call is made.

## E. Canonical Results queue

The Results page now derives review questions and limitation counts from the same project_review_plan used by reports, then adds any unique comparison review item from the global finding gate. This is intended to remove UI/report count drift.

## First acceptance slice — Test 77

Do not run AI and do not re-upload PDFs.

After deploying 18.7:

1. Reboot/open Test 77.
2. Go to `Проверка` and capture the 18.7 info banner:
   - completed cross-section checks / total;
   - strict cross-section coverage percentage.
3. Go to `Результаты` and capture:
   - raw specialist questions;
   - number of work packages;
   - compression percentage;
   - verified count;
   - system limitations.
4. Verify Compressor 54.3 vs 48.7 remains a PROJECT_FINDING.
5. Verify Building 89.9 vs Dedusting module 23.5 remain separate and matching values can become VERIFIED_OK only from independent addressable evidence.

## Acceptance principle

18.7 is accepted only if strict coverage rises without increasing false positives and the review queue becomes materially smaller as work packages while all raw questions remain traceable.
