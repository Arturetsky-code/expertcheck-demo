# ExpertCheck 7.3 Alpha 1.4 — Composition Registry Fail-Safe

## Critical change
The engineer-facing project composition is no longer reconstructed from generic text candidates.
If an explicit project composition source exists, the primary registry is built directly from:

1. PZ complex-object register (`Сведения о сложном объекте`);
2. General-plan explication (`Экспликация зданий и сооружений/площадок`).

Generic narrative extraction can enrich the model but cannot delete or replace these structured rows.

## General plan evidence
Explication entries are now marked as `OBJECT_REGISTER` evidence and receive the lifecycle status parsed from the explication. This prevents Object Intelligence from treating short legitimate names such as КПП/КТП as weak narrative candidates.

## UI fail-safe
`studio.data.raw_registry()` prefers `composition_baseline` when it is present. Generic candidates are not shown in the primary composition editor while a structured baseline exists.

## Regression coverage
The regression suite includes the four supplied general plans and the supplied PZ. It checks that structured GP/PZ rows survive even when generic Object Intelligence would otherwise reject them.
