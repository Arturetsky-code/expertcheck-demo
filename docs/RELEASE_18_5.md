# ExpertCheck 18.5 Candidate · Evidence Quality

## Goal

18.5 moves the main development focus from AI runtime resilience to engineering evidence quality.

The release intentionally limits scope to the Assignment/Checklist semantic evidence vertical:

Requirement → bounded evidence window → entity/property binding → Judge → Critic → local fail-closed gate.

It does not redesign NTD, Drawing Intelligence, or the cross-section engine.

## Changes

### 1. Anchor-focused Evidence Windowing

Earlier semantic retrieval could locate a relevant long clause correctly, but the outbound Judge payload always used the first 720 characters of that clause. The actual project decision could therefore be cut off.

18.5:
- builds lexical anchors from the atomic requirement, expected entity, property name and critical qualifiers;
- selects the densest bounded window around those anchors;
- sends up to ~960 characters of that focused window instead of blindly truncating the prefix;
- preserves document aliases and bounded pseudonymised payloads.

### 2. Strong entity binding

Object identity now:
- preserves short project identifiers such as ДСК / ККВ / ПС;
- removes generic nouns such as «здание», «площадка», «система» from identity proof;
- respects GP/position mismatch when both sides provide a position;
- treats a generic owner without a discriminating identifier as UNPROVEN rather than MATCHED.

For contracts with requires_same_owner=true, L4 requires a deterministic owner match.

### 3. Strong property binding

For contracts with requires_same_parameter=true:
- L4 requires deterministic property_match=true;
- same value/unit or semantic similarity cannot substitute for metric identity;
- Judge categorical SUPPORTS/CONTRADICTS is blocked locally if the cited evidence does not deterministically confirm the property.

### 4. Judge contract

The Judge prompt now explicitly treats ExpertCheck binding fields as higher-priority machine-readable evidence:
- owner mismatch → OTHER_ENTITY;
- property mismatch → OTHER_METRIC;
- unresolved required binding → INSUFFICIENT.

The local validator independently enforces the same rule after the model response.

### 5. Checkpoint compatibility

18.4.x Judge/Critic decisions are not reused automatically after the evidence-window/binding contract changes.

The PDF corpus and deterministic extraction are retained, but the semantic AI layer is revalidated under 18.5.

Provider qualification contract version is also advanced because the Judge contract changed.

### 6. Technical diagnostics

Technical report gains the sheet:

**AI — качество evidence**

It contains:
- packet/domain;
- requirement;
- expected entity/property;
- actual bounded evidence window;
- source/evidence_id;
- retrieval score;
- entity/property binding state;
- observed entity/property;
- contract-ready flag;
- missing critical qualifiers.

### 7. UX

When AI is complete, «Пересчитать результаты из цифрового снимка» is no longer a primary red action. It is moved into **Дополнительные действия**.

## Acceptance strategy

Do not start with another full 12-document AI run.

First acceptance slice:
1. Open the saved DSK Test 77 corpus in 18.5.
2. Confirm that 18.4.x AI checkpoint is shown as requiring revalidation, without reparsing PDFs.
3. Run one continuation slice only.
4. Export the technical report.
5. Review 10–15 Assignment packets in **AI — качество evidence**.

Primary quality questions:
- Did late project decisions remain visible in the Judge window?
- Did false OTHER_ENTITY caused by truncated text decrease?
- Did false metric binding remain blocked?
- Did any SUPPORTS occur without deterministic object/property proof where the contract requires it?
- Are 89.9 / 23.5 row-binding protections unchanged?

Only after this slice is accepted should the full 12-document semantic queue be completed.

## Regression targets

- No categorical verdict from same-number/different-metric evidence.
- No object-specific L4 from a generic object noun alone.
- Short project codes remain available for entity identity.
- Outbound project evidence remains bounded and document names remain pseudonymised.
- Fail-closed L5 policy remains unchanged.
