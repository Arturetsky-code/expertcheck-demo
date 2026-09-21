# ExpertCheck 25.0 Alpha 1 Unified Verification Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first production vertical slice of ExpertCheck 25.0 where every Design Assignment result flows through one strict `Requirement -> Route -> Evidence -> Binding -> Proof -> Decision -> Trace` pipeline.

**Architecture:** Add a new `core25` package beside stable `core20`. Reuse proven `core20` extraction/routing outputs only through adapters; categorical decisions are owned by `core25` integrity gates. Start with Design Assignment verification, then freeze Test 78 defects as Golden Set regressions.

**Tech Stack:** Python 3, dataclasses/enums, pytest, existing ExpertCheck `core20` canonical model and regression fixtures.

**Spec:** `docs/superpowers/specs/2026-09-17-expertcheck-25-quality-leap.md`

## Global Constraints

- Stable baseline branch remains `codex/expertcheck-20.0` at `6afaf020f329f07bdbce6d0ea2c0e1238023aed6`.
- Implementation branch is `codex/expertcheck-25.0-quality-leap`.
- No categorical verdict without addressable canonical evidence.
- No categorical verdict without proven binding when ownership is required.
- Table-of-contents/generic/unaddressable evidence is never sufficient proof.
- AI/Judge/Critic confidence or success cannot bypass deterministic integrity gates.
- `REVIEW` and `LIMITATION` are valid terminal outcomes.
- Existing `core20` regressions must remain green.
- TDD is mandatory for production behavior changes.

---

### Task 1: Core contracts and categorical decision integrity gate

**Files:**
- Create: `core25/__init__.py`
- Create: `core25/contracts.py`
- Create: `core25/integrity.py`
- Create: `tests/core25/test_integrity_gate.py`

**Interfaces:**
- Produces: `DecisionState`, `BindingState`, `EvidenceRef`, `Binding`, `Proof`, `Decision`, `DecisionRequest`.
- Produces: `enforce_decision_integrity(request: DecisionRequest) -> Decision`.
- Later tasks rely on categorical decisions being downgraded to `REVIEW` when proof preconditions are not met.

- [ ] **Step 1: Write the failing tests**

```python
from core25.contracts import (
    Binding,
    BindingState,
    DecisionRequest,
    DecisionState,
    EvidenceRef,
    Proof,
)
from core25.integrity import enforce_decision_integrity


def test_categorical_decision_requires_addressable_evidence():
    evidence = EvidenceRef(
        evidence_id="E1",
        document_id="PZ",
        page=12,
        fragment="Производительность ДСК 500 т/ч",
        addressable=False,
        source_kind="GENERIC_SEARCH_HIT",
    )
    binding = Binding(
        binding_id="B1",
        evidence_id="E1",
        object_id="DSK",
        parameter_code="CAPACITY",
        state=BindingState.PROVEN,
    )
    proof = Proof(proof_id="P1", evidence_ids=("E1",), binding_ids=("B1",), valid=True)

    result = enforce_decision_integrity(
        DecisionRequest(
            requested_state=DecisionState.COMPLIANT,
            evidence=(evidence,),
            bindings=(binding,),
            proof=proof,
            ownership_required=True,
        )
    )

    assert result.state is DecisionState.REVIEW
    assert result.reason_code == "ADDRESSABLE_EVIDENCE_REQUIRED"


def test_categorical_decision_requires_proven_binding_when_owner_required():
    evidence = EvidenceRef(
        evidence_id="E1",
        document_id="PZ",
        page=12,
        fragment="Производительность ДСК 500 т/ч",
        addressable=True,
        source_kind="PAGE_FRAGMENT",
    )
    binding = Binding(
        binding_id="B1",
        evidence_id="E1",
        object_id="DSK",
        parameter_code="CAPACITY",
        state=BindingState.CANDIDATE,
    )
    proof = Proof(proof_id="P1", evidence_ids=("E1",), binding_ids=("B1",), valid=True)

    result = enforce_decision_integrity(
        DecisionRequest(
            requested_state=DecisionState.NONCOMPLIANT,
            evidence=(evidence,),
            bindings=(binding,),
            proof=proof,
            ownership_required=True,
        )
    )

    assert result.state is DecisionState.REVIEW
    assert result.reason_code == "PROVEN_BINDING_REQUIRED"


def test_review_is_allowed_without_proof():
    result = enforce_decision_integrity(
        DecisionRequest(
            requested_state=DecisionState.REVIEW,
            evidence=(),
            bindings=(),
            proof=None,
            ownership_required=True,
        )
    )
    assert result.state is DecisionState.REVIEW
```

- [ ] **Step 2: Run tests to verify RED**

Run: `pytest tests/core25/test_integrity_gate.py -q`

Expected: FAIL during import because `core25` contracts/integrity do not exist yet.

- [ ] **Step 3: Implement minimal contracts and gate**

`core25/contracts.py` must define string enums and frozen dataclasses with exactly the fields used by the tests. `DecisionState` values: `COMPLIANT`, `NONCOMPLIANT`, `REVIEW`, `LIMITATION`. `BindingState` values: `CANDIDATE`, `PROVEN`, `REJECTED`.

`core25/integrity.py` must apply this order for categorical requests:
1. at least one referenced evidence item is addressable;
2. if ownership is required, every binding used by proof is `PROVEN`;
3. proof exists and `proof.valid` is true;
4. otherwise downgrade to `REVIEW` with deterministic reason code.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `pytest tests/core25/test_integrity_gate.py -q`

Expected: `3 passed`.

- [ ] **Step 5: Run legacy proof regression**

Run: `pytest test_core20_alpha1013_proof_trace.py test_core20_alpha1012_evidence_quality.py -q`

Expected: all existing tests pass.

- [ ] **Step 6: Commit**

```bash
git add core25 tests/core25/test_integrity_gate.py
git commit -m "feat(core25): add verification contracts and integrity gate"
```

---

### Task 2: Requirement contract and core20 adapter

**Files:**
- Modify: `core25/contracts.py`
- Create: `core25/adapters/__init__.py`
- Create: `core25/adapters/core20.py`
- Create: `tests/core25/test_core20_requirement_adapter.py`

**Interfaces:**
- Produces: `AtomicRequirement`.
- Produces: `adapt_core20_requirement(requirement) -> AtomicRequirement`.
- Consumes existing `core20.model.Requirement` without modifying `core20`.

- [ ] **Step 1: Write failing test**

```python
from core20.model import Requirement
from core25.adapters.core20 import adapt_core20_requirement


def test_core20_requirement_adapter_preserves_route_and_parameter():
    source = Requirement(
        requirement_id="R1",
        domain="assignment",
        text="Производительность ДСК 500 т/ч",
        target_object_id="DSK",
        expected_parameter_code="CAPACITY",
        expected_evidence_route=["ТХ"],
        required_slots=["OBJECT", "PARAMETER", "VALUE"],
        verification_kind="NUMERIC",
    )

    result = adapt_core20_requirement(source)

    assert result.requirement_id == "R1"
    assert result.domain == "assignment"
    assert result.target_object_id == "DSK"
    assert result.parameter_code == "CAPACITY"
    assert result.expected_routes == ("ТХ",)
    assert result.required_proof_slots == ("OBJECT", "PARAMETER", "VALUE")
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/core25/test_core20_requirement_adapter.py -q`

Expected: FAIL because adapter and `AtomicRequirement` are missing.

- [ ] **Step 3: Implement minimal adapter**

Add frozen `AtomicRequirement` contract with fields: `requirement_id`, `domain`, `text`, `atomic_condition`, `verification_kind`, `target_object_id`, `parameter_code`, `expected_routes`, `required_proof_slots`, `metadata`.

Adapter copies normalized data only; it must not calculate verdicts or mutate `core20`.

- [ ] **Step 4: Verify GREEN**

Run: `pytest tests/core25/test_core20_requirement_adapter.py -q`

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add core25/contracts.py core25/adapters tests/core25/test_core20_requirement_adapter.py
git commit -m "feat(core25): adapt core20 requirements into unified contracts"
```

---

### Task 3: Evidence eligibility and table-of-contents rejection

**Files:**
- Create: `core25/evidence.py`
- Create: `tests/core25/test_evidence_eligibility.py`

**Interfaces:**
- Produces: `eligible_for_proof(evidence: EvidenceRef) -> tuple[bool, str]`.
- Produces deterministic reason codes used by proof construction.

- [ ] **Step 1: Write failing tests**

```python
from core25.contracts import EvidenceRef
from core25.evidence import eligible_for_proof


def test_table_of_contents_never_qualifies_as_proof():
    evidence = EvidenceRef(
        evidence_id="TOC1",
        document_id="PZ",
        page=2,
        fragment="Содержание: Технологические решения ... 45",
        addressable=True,
        source_kind="TABLE_OF_CONTENTS",
    )
    ok, reason = eligible_for_proof(evidence)
    assert ok is False
    assert reason == "TOC_NOT_PROOF"


def test_addressable_page_fragment_can_be_proof_candidate():
    evidence = EvidenceRef(
        evidence_id="E2",
        document_id="TH",
        page=18,
        fragment="Проектная производительность комплекса составляет 500 т/ч.",
        addressable=True,
        source_kind="PAGE_FRAGMENT",
    )
    ok, reason = eligible_for_proof(evidence)
    assert ok is True
    assert reason == "ELIGIBLE"
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/core25/test_evidence_eligibility.py -q`

Expected: FAIL because `core25.evidence` does not exist.

- [ ] **Step 3: Implement minimal evidence gate**

Reject source kinds `TABLE_OF_CONTENTS`, `GENERIC_SEARCH_HIT`, `AI_SUMMARY`, `UNADDRESSED_TEXT`. Reject any `addressable=False`. Allow other addressable fragments.

- [ ] **Step 4: Verify GREEN and previous core25 tests**

Run: `pytest tests/core25 -q`

Expected: all current `core25` tests pass.

- [ ] **Step 5: Commit**

```bash
git add core25/evidence.py tests/core25/test_evidence_eligibility.py
git commit -m "feat(core25): enforce proof evidence eligibility"
```

---

### Task 4: Owner/parameter binding gate

**Files:**
- Create: `core25/binding.py`
- Create: `tests/core25/test_binding.py`

**Interfaces:**
- Produces: `prove_binding(requirement: AtomicRequirement, evidence: EvidenceRef, *, evidence_object_id: str | None, evidence_parameter_code: str | None) -> Binding`.
- Binding becomes `PROVEN` only when required owner and parameter identities match.

- [ ] **Step 1: Write failing regression tests**

```python
from core25.binding import prove_binding
from core25.contracts import AtomicRequirement, BindingState, EvidenceRef


def _req():
    return AtomicRequirement(
        requirement_id="R-AREA",
        domain="assignment",
        text="Площадь здания проборазделки 89,9 м2",
        atomic_condition="Площадь здания проборазделки = 89,9 м2",
        verification_kind="NUMERIC",
        target_object_id="PROBE_BUILDING",
        parameter_code="AREA",
        expected_routes=("АР",),
        required_proof_slots=("OBJECT", "PARAMETER", "VALUE"),
    )


def test_same_parameter_but_wrong_owner_is_rejected():
    evidence = EvidenceRef(
        evidence_id="E-DUST",
        document_id="AR",
        page=17,
        fragment="Модуль обеспыливания. Площадь 23,5 м2",
        addressable=True,
        source_kind="PAGE_FRAGMENT",
    )
    result = prove_binding(
        _req(),
        evidence,
        evidence_object_id="DUST_MODULE",
        evidence_parameter_code="AREA",
    )
    assert result.state is BindingState.REJECTED
    assert result.reason_code == "OWNER_MISMATCH"


def test_same_owner_and_parameter_can_be_proven():
    evidence = EvidenceRef(
        evidence_id="E-PROBE",
        document_id="AR",
        page=15,
        fragment="Здание проборазделки. Площадь 89,9 м2",
        addressable=True,
        source_kind="PAGE_FRAGMENT",
    )
    result = prove_binding(
        _req(),
        evidence,
        evidence_object_id="PROBE_BUILDING",
        evidence_parameter_code="AREA",
    )
    assert result.state is BindingState.PROVEN
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/core25/test_binding.py -q`

Expected: FAIL because binding engine is missing.

- [ ] **Step 3: Implement minimal binding rules**

Rules:
- evidence must first pass `eligible_for_proof`;
- if requirement has `target_object_id`, evidence owner must match exactly after adapter normalization;
- if requirement has `parameter_code`, evidence parameter must match exactly after uppercase normalization;
- mismatch is `REJECTED`, not weakly scored;
- matching required identities yields `PROVEN`.

- [ ] **Step 4: Verify GREEN**

Run: `pytest tests/core25 -q`

Expected: all current tests pass.

- [ ] **Step 5: Commit**

```bash
git add core25/binding.py tests/core25/test_binding.py
git commit -m "feat(core25): add strict owner parameter binding"
```

---

### Task 5: Canonical proof, decision state machine, and trace

**Files:**
- Create: `core25/proof.py`
- Create: `core25/decision.py`
- Create: `core25/pipeline.py`
- Create: `tests/core25/test_vertical_pipeline.py`

**Interfaces:**
- Produces: `build_proof(requirement, evidence, bindings) -> Proof`.
- Produces: `decide(requirement, proof, evidence, bindings, requested_state) -> Decision`.
- Produces: `verify_requirement(...) -> VerificationTrace` containing requirement, route, evidence ids, binding ids, proof id, decision.

- [ ] **Step 1: Write failing vertical tests**

```python
from core25.contracts import AtomicRequirement, DecisionState, EvidenceRef
from core25.pipeline import verify_requirement


def test_vertical_slice_returns_traceable_compliant_decision():
    requirement = AtomicRequirement(
        requirement_id="R1",
        domain="assignment",
        text="Производительность ДСК 500 т/ч",
        atomic_condition="CAPACITY = 500 t/h",
        verification_kind="NUMERIC",
        target_object_id="DSK",
        parameter_code="CAPACITY",
        expected_routes=("ТХ",),
        required_proof_slots=("OBJECT", "PARAMETER", "VALUE"),
    )
    evidence = EvidenceRef(
        evidence_id="E1",
        document_id="TH",
        page=18,
        fragment="Производительность ДСК составляет 500 т/ч",
        addressable=True,
        source_kind="PAGE_FRAGMENT",
    )

    trace = verify_requirement(
        requirement=requirement,
        evidence=(evidence,),
        evidence_bindings={"E1": {"object_id": "DSK", "parameter_code": "CAPACITY"}},
        requested_state=DecisionState.COMPLIANT,
    )

    assert trace.decision.state is DecisionState.COMPLIANT
    assert trace.decision.evidence_ids == ("E1",)
    assert trace.proof is not None
    assert trace.proof.valid is True


def test_ai_requested_success_cannot_bypass_missing_binding():
    requirement = AtomicRequirement(
        requirement_id="R2",
        domain="assignment",
        text="Площадь здания проборазделки 89,9 м2",
        atomic_condition="AREA = 89.9 m2",
        verification_kind="NUMERIC",
        target_object_id="PROBE_BUILDING",
        parameter_code="AREA",
        expected_routes=("АР",),
        required_proof_slots=("OBJECT", "PARAMETER", "VALUE"),
    )
    evidence = EvidenceRef(
        evidence_id="E2",
        document_id="AR",
        page=17,
        fragment="Модуль обеспыливания. Площадь 23,5 м2",
        addressable=True,
        source_kind="PAGE_FRAGMENT",
    )

    trace = verify_requirement(
        requirement=requirement,
        evidence=(evidence,),
        evidence_bindings={"E2": {"object_id": "DUST_MODULE", "parameter_code": "AREA"}},
        requested_state=DecisionState.COMPLIANT,
    )

    assert trace.decision.state is DecisionState.REVIEW
    assert trace.decision.reason_code in {"PROVEN_BINDING_REQUIRED", "PROOF_INVALID"}
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/core25/test_vertical_pipeline.py -q`

Expected: FAIL because proof/decision/pipeline modules are missing.

- [ ] **Step 3: Implement minimal vertical pipeline**

The pipeline must:
1. preserve requirement identity;
2. evaluate evidence eligibility;
3. create bindings through `prove_binding`;
4. construct proof only from eligible evidence and `PROVEN` bindings;
5. mark proof invalid if any required proof slot cannot be satisfied;
6. send requested categorical state through `enforce_decision_integrity`;
7. return a trace object containing all ids needed to reproduce the decision.

- [ ] **Step 4: Verify GREEN**

Run: `pytest tests/core25 -q`

Expected: all current tests pass.

- [ ] **Step 5: Commit**

```bash
git add core25/proof.py core25/decision.py core25/pipeline.py tests/core25/test_vertical_pipeline.py
git commit -m "feat(core25): add unified requirement verification pipeline"
```

---

### Task 6: Freeze Test 78 defects as Golden Set regressions

**Files:**
- Create: `tests/core25/golden/__init__.py`
- Create: `tests/core25/golden/test_test78_integrity.py`
- Reuse: existing Alpha 10.1.2/10.1.3 regression semantics; do not copy obsolete implementation assumptions.

**Interfaces:**
- Golden Set tests call public `core25` contracts/pipeline only.
- No test may depend on UI rendering.

- [ ] **Step 1: Add one regression test per permanent defect class**

Required cases:
- table of contents as evidence -> categorical verdict forbidden;
- wrong object / right parameter -> binding rejected;
- missing owner section -> `REVIEW` or `LIMITATION`;
- persistence round-trip preserves evidence/binding/proof ids;
- Judge/Critic positive text without proof -> categorical verdict forbidden;
- provider 429/unavailable -> not completed-success state;
- `nan` confidence/value never becomes proof data;
- canonical proof must be selected for categorical result.

- [ ] **Step 2: Verify new Golden Set fails for any unsupported contract**

Run: `pytest tests/core25/golden -q`

Expected: any not-yet-supported case must fail for a concrete missing behavior, not because of fixture errors.

- [ ] **Step 3: Implement only missing contract behavior**

Extend `core25` modules in the smallest scope needed by the failing test. Do not add UI or new domain features.

- [ ] **Step 4: Verify Golden Set and all core25 tests**

Run: `pytest tests/core25 -q`

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add core25 tests/core25/golden
git commit -m "test(core25): freeze Test 78 defects as Golden Set"
```

---

### Task 7: Design Assignment 56-requirement vertical integration

**Files:**
- Create: `core25/requirement_engine.py`
- Create: `core25/routing.py`
- Extend: `core25/adapters/core20.py`
- Create: `tests/core25/test_assignment_56_contract.py`

**Interfaces:**
- Produces: `prepare_assignment_requirements(core20_requirements) -> tuple[AtomicRequirement, ...]`.
- Produces: `route_requirement(requirement) -> RouteDecision` with either explicit expected routes or explicit route limitation.

- [ ] **Step 1: Write failing 56-requirement contract test**

The test must load the existing DSK assignment regression input already used by the repository and assert:

```python
assert len(requirements) == 56
assert all(item.verification_kind for item in requirements)
assert all(item.expected_routes or item.metadata.get("route_limitation") for item in requirements)
assert len({item.requirement_id for item in requirements}) == 56
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/core25/test_assignment_56_contract.py -q`

Expected: FAIL because 25.0 preparation/routing is not implemented.

- [ ] **Step 3: Implement requirement preparation and route adaptation**

Preserve the 56 atomic requirements already reconstructed by the evidence-driven assignment engine. Do not re-parse the source PDF in Alpha 1 if a verified structured requirement set is already available; adapt and normalize it.

Every requirement must receive:
- verification kind;
- expected route(s), or a route limitation reason;
- target owner if known;
- parameter/decision code if known;
- required proof slots.

- [ ] **Step 4: Verify GREEN**

Run: `pytest tests/core25/test_assignment_56_contract.py tests/core25 -q`

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add core25/requirement_engine.py core25/routing.py core25/adapters/core20.py tests/core25/test_assignment_56_contract.py
git commit -m "feat(core25): route all 56 assignment requirements through unified core"
```

---

### Task 8: Alpha 1 regression gate and release evidence

**Files:**
- Create: `RELEASE_NOTES_250_ALPHA1.md`
- Create: `VALIDATION_250_ALPHA1.json`
- Modify CI workflow only if existing workflow does not automatically include `tests/core25`.

**Interfaces:**
- Validation JSON records exact test counts and acceptance-gate results.

- [ ] **Step 1: Run new core**

Run: `pytest tests/core25 -q`

Expected: PASS.

- [ ] **Step 2: Run legacy integrity regressions**

Run: `pytest test_core20_alpha1012_evidence_quality.py test_core20_alpha1013_proof_trace.py -q`

Expected: PASS.

- [ ] **Step 3: Run full repository test suite**

Run: `pytest -q`

Expected: PASS except only pre-documented external-fixture skips; no new failures.

- [ ] **Step 4: Validate Alpha 1 acceptance gate**

Record explicit booleans for all ten acceptance conditions from the spec. A failed condition keeps release status `NOT_READY` even if pytest is green.

- [ ] **Step 5: Write release notes and validation JSON**

`VALIDATION_250_ALPHA1.json` must include branch, HEAD, test commands/results, 56-requirement counts, categorical decisions with proof counts, review/limitation counts, Golden Set result, and `release_gate`.

- [ ] **Step 6: Commit**

```bash
git add RELEASE_NOTES_250_ALPHA1.md VALIDATION_250_ALPHA1.json .github/workflows
git commit -m "release: validate ExpertCheck 25.0 Alpha 1"
```

---

## Self-review

- Spec coverage: all Alpha 1 architecture invariants and acceptance conditions have an implementing task.
- Placeholder scan: no TODO/TBD implementation placeholders are used.
- Type consistency: `EvidenceRef`, `Binding`, `Proof`, `Decision`, `AtomicRequirement`, and `DecisionState` are introduced before downstream use.
- Migration safety: no task modifies stable `core20` behavior; integration occurs through adapters.
- Quality safety: raw automatic coverage is never used as a substitute for proof integrity.
