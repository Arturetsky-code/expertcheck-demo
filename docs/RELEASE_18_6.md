# ExpertCheck 18.6 Candidate · Project Knowledge Recovery

## Goal

Restore the deterministic engineering model after snapshot/PostgreSQL recovery without reparsing source PDFs.

18.6 deliberately moves development away from semantic queue migration and back to project understanding:

- trusted object registry;
- object passports and TEP characteristics;
- Project Understanding object → property → evidence model;
- raw cross-section comparisons;
- compact Project Knowledge manifest.

## Root cause fixed

18.4.x analysis snapshots already contained trusted object_registry and raw comparisons inside analysis_snapshot.quality_gate_inputs. The restore path did not lift those structures back into the engineer-facing model. As a result a restored project could show Objects=0 / TEP=0 and block cross-section review even though the deterministic data still existed in the snapshot.

## 18.6 behavior

On restored projects ExpertCheck now:

1. lifts the embedded trusted registry into consolidated_registry when the latter is missing;
2. restores raw cross-section comparisons when the public result collection is empty;
3. rebuilds object passports from restored registry + preserved findings;
4. rebuilds Project Understanding deterministically from the same evidence;
5. creates a compact Project Knowledge manifest with object index and component counts;
6. populates object assembly candidates in the normal UI path;
7. keeps object_registry_confirmed=false unless the user had explicitly confirmed it before;
8. persists the self-healed model to PostgreSQL using the workspace signature.

New snapshots also export the object-model components directly so later restores do not need fallback reconstruction.

## Memory policy

Project Knowledge Model is a compact manifest. Heavy registry/passport/comparison structures remain in their canonical fields and are not duplicated inside the manifest.

## First acceptance slice — Test 77

Do not run AI and do not re-upload PDFs.

After deploying 18.6:

1. Open the existing PostgreSQL project Test 77.
2. The project header should show recovered object/TEP candidates instead of zeroes.
3. Open object confirmation and verify that the recovered registry is populated.
4. Confirm the composition once.
5. Verify that passports and cross-section review become available.

Only after this passes, inspect two deterministic control cases:

- Compressor / AREA_BUILD: PZ 54.3 m² vs PZU 48.7 m² — conflict must be visible even when the correct/current value is not yet verified;
- Sample preparation building 89.9 m² vs Dedusting module 23.5 m² — values must remain attached to different objects/rows.

## Out of scope

- Issue #4 stale semantic OTHER_ENTITY checkpoint migration remains known technical debt.
- NTD coverage is not redesigned in 18.6.
- Drawing Intelligence is not redesigned in 18.6.
- No new provider/model is introduced.
