# ExpertCheck 25.2 — Local Test 78 handoff

Date: 2026-09-23
Branch: `codex/expertcheck-25.2-coverage-breakthrough`

## Remote state already committed

25.2 Alpha 2 / Evidence Admission Breakthrough is committed to GitHub.
The last substantive validated code point was `0c8b3c6ff30e1ad89d385c5043b61ff730a47859`.
Release/validation metadata followed through `aa1643ffc49f337b53e1ea22a59e13468209708f`.
A later workflow-only commit `dec7aa9d08b2b0b79137d7b627934f7371d43e5d`
added a short-lived source snapshot artifact workflow for local Test 78 work.

Validated remote gates at the Alpha 2 code point:
- Core25: 91 passed / 0 failed
- Core20 regression: 95 passed / 0 failed
- Core20 main: 95 passed / 0 failed
- Results/report integrity: 17 passed / 0 failed
- Full release gate: success; 0 new/unclassified blockers

## Test 78 package

Real 12-file Test 78 package was provided by the user and used locally.
Initial full deterministic run used the real `analyze_uploaded` pipeline with AI off.

## Local benchmark history

### First full Alpha 2 local run
- Runtime: about 7 min 28 sec
- Requirements produced: 57 (unexpected; historical benchmark is 56)
- "Соответствует заданию": 15
- "Требует проверки": 42
- "Отклонение": 0
- Apparent categorical coverage: 15/57 = 26.3%
- AI: off

This 15/57 result was NOT accepted as trustworthy after audit.

False-positive classes found during audit:
1. A requirement like "Срок строительства определить проектной документацией"
   was closed from a table-of-contents / heading-like passage rather than a
   substantive project decision.
2. Several distinct "не требуется" requirements were incorrectly closed from
   the same unrelated negative phrase about compensation/losses.

Therefore the rule became: never optimize the count at the expense of proof quality.

### Fast local benchmark mode
The PDF corpus was cached locally; repeat deterministic runs became approximately
10–15 seconds instead of 7–8 minutes.

The requirement atomization was brought back to the expected 56 requirements.

### Latest local benchmark before handoff
Latest working local point reported:
- 22 requirements: "Соответствует заданию"
- 3 requirements: categorical deviations / proven mismatches
- 31 requirements: still require review
- Total categorical: 25/56
- Strict categorical coverage: 44.6%
- AI: off

IMPORTANT: final manual audit of all 25 categorical results was NOT completed
before the chat handoff. Treat 25/56 as a promising provisional benchmark, not
a release claim.

## Main local findings / work direction

1. The major bottleneck shifted from retrieval to evidence admission.
2. Earlier 25.2 Alpha 1 had 48/56 requirements with at least one directed
   evidence candidate but only 5/56 categorical.
3. Alpha 2 targeted:
   - unresolved safe scopes,
   - duplicate owner IDs,
   - PDF word-wrap hyphenation,
   - mixed positive/negative requirements,
   - short presence requirements,
   - concept-vs-generic evidence precedence,
   - support-wall owner/routing,
   - AR/PZ routing for canopies and modular buildings,
   - per-requirement admission diagnostics.
4. Admission diagnostics now distinguish:
   - NO_CANDIDATE
   - CANDIDATE_NOT_VERIFIED
   - CANONICAL_OR_SECTION_FILTER
   - BINDING_BLOCKED
   - PROOF_BLOCKED
   - PROVEN
5. One next high-value executor identified:
   `LIME_SUPPLY_SYSTEM` for the lime feed system requirement. The project
   appears to contain addressable evidence across TX/KR/drawings for bunkers,
   big-bags, vehicle delivery, 3.2 t electric crane beam, open canopy and
   maintenance platforms. This was being prepared but not finalized at handoff.
6. Remaining 31 requirements should next be divided into:
   - impossible on the 12-file package because the profile section is absent;
   - profile section present, but ExpertCheck still fails to close the proof.

## Process rule going forward

Do NOT deploy every alpha to Streamlit.
Development loop should be:
code -> local Test 78 -> audit categorical results -> patch -> local Test 78.

Streamlit is reserved for a build that shows a substantial, audited improvement.
Target before asking the user to redeploy: at least 25–30 trustworthy categorical
requirements out of 56 (roughly 45–55%), with false-positive audit completed.

## Handoff caution

The latest 25/56 benchmark included local experimental work after the validated
remote Alpha 2 point. Do not assume every local experimental change that
contributed to that number is already committed to GitHub. Before continuing
development, compare the current branch against this handoff and reconstruct /
commit any local-only changes needed to reproduce the 25/56 benchmark.
