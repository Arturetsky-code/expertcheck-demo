# WIP checkpoint — PROJECT_DURATION

Date: 2026-09-23
Validated baseline: 20/56, see DEVELOPMENT_STATE.md
Status: WIP — not yet promoted to validated benchmark.

Goal:
- close Assignment row 10 where the construction duration is explicitly left to project documentation;
- accept only addressable numeric duration values from profile project sources;
- continue rejecting TOC/headings and generic construction mentions.

Observed Test 78 evidence:
- PZ contains a structured project fact equivalent to:
  - «Сведения о сроках проведения работ»
  - «Продолжительность работ, месяц: 12»

Local implementation direction in core/assignment_verification_kernel.py:
- DESIGN_DETERMINED construction-duration parser accepts both:
  - «12 месяцев»
  - structured field «Продолжительность работ, месяц: 12»
- structured duration requires the local subject chain «сведения / сроки / проведение работ / продолжительность работ»;
- DESIGN_MARKERS are not required only for this structured fact shape;
- evidence stores:
  - design_determined_subject = CONSTRUCTION_DURATION
  - structured_project_fact = true
  - observed_value
  - observed_unit

Important:
- This WIP is not yet a validated 21/56 checkpoint.
- Core25 still needs a dedicated proof route for DESIGN_DETERMINED structured project facts; the legacy executor finds the correct value, but current Core25 proof semantics may still reduce it to ordinary PRESENCE and block L5.
- Resume from this exact issue in a fresh chat; do not restart duration discovery.

Relevant local diff excerpt:

```diff
+ structured_duration = False
  if construction_duration:
-   duration_value = re.search(r"...number before unit...", low)
+   duration_value = (
+       re.search(r"...number before unit...", low)
+       or re.search(r"(?:мес...|дн...|год...)[ :=-]*number", low)
+   )
    duration_subject = ...
+   structured_duration = bool(
+       "сведени" in low and "срок" in low and "проведен" in low and "работ" in low
+       and re.search(r"продолжительност\w*\s+работ\w*[^\d]{0,40}\d+(?:[,.]\d+)?", low)
+   )
+   if not (duration_value and (duration_subject or structured_duration)):
+       continue

- if not any(marker in low for marker in DESIGN_MARKERS):
+ if not structured_duration and not any(marker in low for marker in DESIGN_MARKERS):
    continue

+ evidence["design_determined_subject"] = "CONSTRUCTION_DURATION"
+ evidence["structured_project_fact"] = selected_structured_duration
+ evidence["observed_value"] = observed_value
+ evidence["observed_unit"] = "месяц"
```

Next step:
1. add Core25 proof route for DESIGN_DETERMINED structured facts;
2. run Test 78;
3. manually audit row 10 evidence;
4. run profile + Core25 regressions;
5. if clean and benchmark becomes 21/56, promote to validated checkpoint.
