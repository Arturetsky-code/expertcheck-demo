# ExpertCheck 8.2 Alpha 1.1

- AI user-facing explanations are required in Russian; non-Russian structured replies receive a translation pass.
- Result enums remain machine-stable and are rendered with Russian labels.
- New entity-type invariant: a property/TEP label cannot be a project object.
- Before cross-section comparison, an invalid object hint is repaired only from an authoritative object at the same general-plan position.
- If the object cannot be reliably recovered, the value is excluded from cross-section comparison instead of creating a false mismatch.
