# ExpertCheck 18.4 Candidate · Verification Runtime

18.4 is a focused runtime release built on 18.3 Quality Gates.

## Goals

1. Make free Groq/Gemini participation operational rather than nominal.
2. Keep L5 fail-closed while allowing a real independent advisory Critic before provider qualification.
3. Confirm a genuine cross-section value conflict without pretending the system already knows the correct value.
4. Prevent physical PDF table rows from leaking values into neighboring project objects.

## Runtime changes

### Free AI Queue Engine
- Groq/Gemini semantic packets are sent one at a time.
- Completed packet decisions are written to the existing semantic checkpoint immediately.
- 429 and transient 5xx events receive one bounded wait/retry; unresolved throttling pauses the queue without deleting completed work.
- Successful structured preflight is cached briefly to avoid spending free quota repeatedly during one analysis session.
- Groq calls are paced to reduce 8k-TPM burst failures observed on the DSK control set.

### Advisory independent Critic
- If Groq Judge and Gemini Critic are both operational and actually different providers, Critic is allowed to review Judge even when one/both routes are not L5-qualified.
- Any semantic result produced under this relaxed activation is downgraded back to L4 REVIEW_QUESTION after Critic review.
- Provider qualification remains mandatory for an AI-generated L5 result.

### Cross-section conflict split
- `conflict_confirmed` and `correct_value_verified` are separate facts.
- Two independent trusted addressable sections with the same object/metric and different values may create a deterministic PROJECT_FINDING.
- The finding explicitly states that the correct/current value still requires confirmation from the owner section.

### Hard physical row binding
- `table_row` / `row_index` plus explicit GP position in row text outrank later semantic nearest-object anchors.
- A value physically belonging to position 4.12 is blocked from being attached to 4.13.
- The guard runs both before and after semantic table-scope enrichment.

## DSK acceptance targets

Re-run the same 12-document DSK control set used for 18.3 and compare:
- AI prepared / Judge attempted / Judge responses / Critic attempted / Critic responses;
- number of 429 events and checkpoint reuse;
- Compressor building footprint conflict (54.3 vs 48.7) must be visible as a confirmed conflict if both sources remain trusted/addressable;
- Building of sample preparation must retain 89.9 m²; 23.5 m² from the dedusting module must not enter its admitted/comparison facts;
- L5 AI results must remain zero unless the exact provider/model routes satisfy the current qualification gate.
