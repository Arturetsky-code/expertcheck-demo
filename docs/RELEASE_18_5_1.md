# ExpertCheck 18.5.1 Candidate · Evidence Binding

18.5.1 is a targeted correction after the first 18.5 control slice on Test 77.

## Test findings addressed

- Evidence Windowing worked: the PZU fence evidence now contains the complete decision «Территория площадки ДСК ограждается…».
- The same evidence was incorrectly held at L3 because atomisation called the feature «Ограждение» and the contract treated it as a standalone OBJECT_SPECIFIC owner.
- A restored L3 row could still display an old 18.4 Judge verdict not backed by the current 18.5 checkpoint.
- Report readiness text could show 344 specialist questions while the exported de-duplicated queue contained 345.
- Critic rejection reason/concerns were not visible in the AI decision sheet.
- “AI packages processed” was actually Judge-response progress, not full Judge/Critic package completion.

## Corrections

1. Site features
   - fencing, access/egress and selected territory-layout requirements are routed to PZU;
   - generic site features such as Ограждение/Проезд are SITE_SPECIFIC, not standalone objects;
   - owner identity does not block a site/global contract when requires_same_owner=false.

2. Binding gate
   - owner/property mismatch remains fail-closed when that dimension is required;
   - non-required dimensions no longer reduce evidence readiness or retrieval score;
   - diagnostics report NOT_REQUIRED instead of a misleading MISMATCH.

3. Checkpoint/state
   - the existing 18.5 checkpoint remains compatible to avoid paying the free-provider cost again;
   - row-level Judge/Critic state that has no matching current checkpoint entry is pruned.

4. Critic audit
   - rejected Critic reasons and blocking_concerns are added to semantic consensus reasons and the technical AI decision sheet.

5. Report reconciliation
   - the exported de-duplicated specialist queue becomes the authoritative question count;
   - readiness text is rebuilt from the same count;
   - AI summary distinguishes fully completed packages, Judge responses, Critic responses and remaining AI operations.

## Next acceptance slice

Do not restart the full queue.

After deploying 18.5.1:
- reopen Test 77;
- run one AI continuation slice;
- export the technical appendix;
- verify the fence packet, Critic reasons, specialist-question reconciliation and package-completion counters.
