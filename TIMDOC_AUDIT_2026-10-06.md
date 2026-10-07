# TimDoc audit — 2026-10-06

## Status

This document records product and verification lessons from a manual audit of the
TimDoc demonstration flow performed on 2026-10-06.

The audit is an external-product observation, not a benchmark proving that ExpertCheck
is better or worse than TimDoc. Its purpose is to turn useful observations into
explicit ExpertCheck design constraints and acceptance tests.

## Findings to carry into ExpertCheck

### 1. Validate page type before applying a requirement

A requirement must not be applied merely because its keywords appear on a page.
The system should first establish that the page / sheet type is compatible with the
requirement's evidence route.

Required behavior:
- wrong page type -> no deterministic proof;
- ambiguous page type -> review / system limitation, not automatic finding;
- correct page type + evidence -> normal proof contract may continue.

### 2. "Not found" is not "proved absent"

Failure to retrieve evidence is not proof of non-compliance.

Required behavior:
- no evidence found -> REVIEW_QUESTION or SYSTEM_LIMITATION according to the contract;
- automatic PROJECT_FINDING requires a separate negative/deviation proof contract;
- a failed deterministic fast path must fall back safely where configured.

This rule is consistent with the current fail-closed normative architecture and must
remain a regression invariant.

### 3. Detect contradictions between findings / proof results

The system should identify mutually incompatible conclusions about the same object,
indicator, or requirement instead of presenting both as independent valid findings.

Examples:
- one module says a required feature is present while another says it is absent;
- two sections assign different values to the same owner-bound indicator;
- two findings recommend mutually exclusive corrective actions.

Required behavior:
- contradiction is surfaced explicitly;
- neither conflicting conclusion is silently promoted as final;
- source evidence for both sides remains addressable.

### 4. Keep verified normative sources separate from AI explanation

The normative source, verified clause text, applicability route and proof contract
must remain independent from model-generated interpretation.

Required behavior:
- AI explanation cannot upgrade an unverified normative clause;
- verified source metadata remains traceable without AI;
- semantic explanation is labelled as interpretation, not as the normative source;
- changing AI provider must not change the registered normative basis.

### 5. Preserve exact addressable evidence

A user should be able to move from a result to:
1. the finding / review question;
2. the supporting quotation or extracted value;
3. the original document and page / sheet;
4. the normative source and clause.

Required behavior:
- evidence carries document + page/sheet;
- owner/object binding is retained where available;
- cross-document comparisons preserve evidence from each compared source;
- report/UI must not flatten this chain into an untraceable summary.

### 6. Maintain one controlled registry of project-documentation composition

Composition checks should use one versioned source of truth that takes account of:
- the applicable normative edition;
- transitional provisions;
- project type / applicability;
- document / subsection roles.

Required behavior:
- document-composition logic is not duplicated independently across modules;
- transitional rules can be represented explicitly;
- absence of a separately named file is not automatically treated as absence of
  required content when the normative structure permits another representation.

## UI implication

For a normative result, the target review experience is a side-by-side or tightly
linked view of:
- result / review question;
- evidence quotation or extracted fact;
- original page or drawing sheet;
- normative clause and source status.

The interface should minimize navigation between these four evidence layers.

## Acceptance / regression cases

The following cases should become explicit ExpertCheck tests.

### TDA-01 — Wrong page type

Given a phrase that lexically matches a requirement but appears on an incompatible
page/sheet type, ExpertCheck must not issue deterministic VERIFIED_OK.

### TDA-02 — Missing evidence is not non-compliance

Given an applicable verified requirement and no positive evidence, ExpertCheck must
not create PROJECT_FINDING unless a dedicated negative/deviation proof contract has
proved the violation.

### TDA-03 — Contradictory project values

Given two addressable project sources bound to the same owner with incompatible
values for the same indicator, ExpertCheck must surface the inconsistency and retain
both evidence locations; it must not silently choose one value.

### TDA-04 — Normative source / AI separation

Given a semantic model response that claims compliance, an unverified or incomplete
normative contract must remain non-promotable.

### TDA-05 — Addressability chain

Every promoted normative result should expose enough metadata to trace:
result -> evidence -> document/page -> normative requirement.

### TDA-06 — Composition with transition rule

Given a project whose required composition depends on a transitional provision,
ExpertCheck must resolve the applicable rule version before declaring a component
missing.

### TDA-07 — Conflicting findings

Given two modules producing mutually incompatible conclusions about the same
owner-bound fact, the final result should surface a conflict state rather than two
independent final conclusions.

## Current ExpertCheck mapping as of checkpoint 05556d4a

Already aligned in principle:
- fail-closed normative proof;
- semantic fallback for multiple hybrid contracts;
- owner-bound set / typed proof;
- addressable evidence candidates;
- owner-bound cross-document value consistency;
- verified normative registry separated from semantic proof.

Still requiring explicit implementation / stronger coverage:
- general page-type validation before requirement application;
- contradiction arbitration across findings/modules;
- a formal addressability invariant across UI/report outputs;
- a single versioned composition registry with transitional provisions;
- integrated UI that shows result, evidence, source page and normative clause together.

## Product interpretation

The TimDoc audit supplies useful design and test inputs. It does not by itself prove
competitive superiority of ExpertCheck. Any superiority claim would require a
controlled benchmark on the same document set, requirements and evaluation criteria.
