# ExpertCheck 5.2 — Integrated AI Pipeline

AI is integrated into the engineering workflow as an advisory verification layer.

## Modes
- Off: deterministic Core only.
- Assistant: automatic review of ambiguous object candidates.
- Extended: object review plus verification of suspicious TEP bindings and semantic checklist review.
- Maximum: reserved for expanded project recommendations; it currently includes all Extended checks.

## Safety rules
- AI never upgrades an object to `trusted` without deterministic evidence.
- A high-confidence AI exclusion can block an obvious document/service candidate.
- Suspicious TEP binding is downgraded to `insufficient data`, not reported as a categorical discrepancy.
- Checklist AI works only with selected structured evidence and preserves the original Core status.
- Full PDFs are not sent by the AI Pipeline.
