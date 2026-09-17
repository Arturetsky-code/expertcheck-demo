# ExpertCheck 25.0 Alpha 1 Unified Verification Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first production vertical slice of ExpertCheck 25.0 so all Design Assignment requirements flow through one auditable `Requirement → Route → Evidence → Binding → Proof → Decision → Trace` pipeline.

**Architecture:** Create a new isolated `core25` package next to stable `core20`. `core25` owns strict contracts and orchestration; proven 20.0 functionality is reused only through `core25/adapters/core20.py`. No categorical verdict is permitted without addressable canonical evidence bound to the correct engineering owner and semantic parameter.

**Tech Stack:** Python 3.11+ compatible codebase, dataclasses/enums, pytest, existing `core20` package, existing page-corpus and parameter-contract helpers.

**Spec:** `docs/superpowers/specs/2026-09-17-expertcheck-25-quality-leap-design.md`

## Global Constraints

- Work only on branch `codex/expertcheck-25.0-quality-leap` created from stable `6afaf020f329f07bdbce6d0ea2c0e1238023aed6`.
- Do not modify `core20` behavior unless an adapter-compatible read-only extension is unavoidable and separately regression-tested.
- No production code without a failing test first.
- `COMPLIANT` requires `PROVEN_MATCH`; `NONCOMPLIANT` requires `PROVEN_MISMATCH`.
- Table of contents, section titles, filenames, unaddressable snippets, semantic similarity, AI confidence, or Judge/Critic agreement cannot alone satisfy proof.
- Object-specific requirements require correct engineering owner binding before comparison.
- Project-global requirements may omit object owner only when their verification contract declares `PROJECT_GLOBAL`.
- AI/provider failure must degrade to review/limitation and must never become successful verification.
- Existing core20 regression tests remain mandatory.
- Initial Test 78 Golden Set is mandatory before Alpha 1 acceptance.

---

## File map

### New production package
- `core25/__init__.py` — public Alpha 1 API.
- `core25/contracts.py` — immutable verification contracts and enums.
- `core25/adapters/__init__.py` — adapter namespace.
- `core25/adapters/core20.py` — conversion from existing canonical 20.0 structures/page corpus into 25.0 contracts.
- `core25/requirement_engine.py` — normalize imported Assignment requirements into atomic 25.0 requirements.
- `core25/routing.py` — create verification routes/contracts.
- `core25/evidence.py` — collect and qualify canonical evidence candidates.
- `core25/binding.py` — owner + parameter/concept binding.
- `core25/proof.py` — deterministic proof assembly and fail-closed integrity gates.
- `core25/decision.py` — strict proof-to-decision mapping.
- `core25/pipeline.py` — orchestrate complete vertical slice.
- `core25/persistence.py` — serialize/restore trace-preserving results.
- `core25/report_trace.py` — expose report-safe trace and sanitize user-facing fields.

### New tests
- `tests/core25/test_contracts.py`
- `tests/core25/test_core20_adapter.py`
- `tests/core25/test_requirement_routing.py`
- `tests/core25/test_evidence_gate.py`
- `tests/core25/test_binding.py`
- `tests/core25/test_proof_decision.py`
- `tests/core25/test_assignment_pipeline.py`
- `tests/core25/test_golden_test78.py`
- `tests/core25/test_persistence_report_trace.py`

### New Golden Set data
- `core25/golden/test78_cases.json`

---

### Task 1: Strict contracts and trace model

**Files:**
- Create: `core25/__init__.py`
- Create: `core25/contracts.py`
- Test: `tests/core25/test_contracts.py`

**Interfaces:**
- Produces enums `Domain`, `Scope`, `BindingState`, `ProofState`, `DecisionState`.
- Produces dataclasses `Requirement25`, `Evidence25`, `Binding25`, `Proof25`, `Decision25`, `Trace25`, `VerificationResult25`.
- All later tasks consume these types.

- [ ] **Step 1: Write the failing contract tests**

```python
from core25.contracts import (
    Binding25, BindingState, Decision25, DecisionState, Domain, Evidence25,
    Proof25, ProofState, Requirement25, Scope, Trace25,
)


def test_categorical_decision_requires_matching_proof_state():
    proof = Proof25(proof_id="P1", requirement_id="R1", state=ProofState.INSUFFICIENT)
    try:
        Decision25(decision_id="D1", requirement_id="R1", state=DecisionState.COMPLIANT, proof=proof)
    except ValueError as exc:
        assert "PROVEN_MATCH" in str(exc)
    else:
        raise AssertionError("COMPLIANT accepted without PROVEN_MATCH")


def test_trace_requires_addressable_evidence_for_categorical_decision():
    ev = Evidence25(evidence_id="E1", document="ПЗ.pdf", page=None, fragment="решение", addressable=False)
    binding = Binding25(binding_id="B1", evidence_id="E1", state=BindingState.BOUND, owner_id="OBJ-1", parameter_code="AREA")
    proof = Proof25(proof_id="P1", requirement_id="R1", state=ProofState.PROVEN_MATCH, evidence_ids=("E1",), binding_ids=("B1",))
    decision = Decision25(decision_id="D1", requirement_id="R1", state=DecisionState.COMPLIANT, proof=proof)
    trace = Trace25(requirement_id="R1", evidence=(ev,), bindings=(binding,), proof=proof, decision=decision)
    assert trace.is_categorical_trace_valid() is False
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `pytest tests/core25/test_contracts.py -v`

Expected: import failure because `core25.contracts` does not exist.

- [ ] **Step 3: Implement minimal strict contracts**

Use string enums and frozen dataclasses. Required invariant in `Decision25.__post_init__`:

```python
if self.state is DecisionState.COMPLIANT and self.proof.state is not ProofState.PROVEN_MATCH:
    raise ValueError("COMPLIANT requires PROVEN_MATCH")
if self.state is DecisionState.NONCOMPLIANT and self.proof.state is not ProofState.PROVEN_MISMATCH:
    raise ValueError("NONCOMPLIANT requires PROVEN_MISMATCH")
```

`Trace25.is_categorical_trace_valid()` must return `False` unless every proof evidence id resolves to an evidence record with `addressable=True`, non-empty `document`, integer `page`, and non-empty `fragment`, and every proof binding id resolves to `BindingState.BOUND`.

- [ ] **Step 4: Run contract tests GREEN**

Run: `pytest tests/core25/test_contracts.py -v`

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add core25 tests/core25/test_contracts.py
git commit -m "feat(core25): add strict verification contracts"
```

---

### Task 2: Core20 adapter and Assignment import

**Files:**
- Create: `core25/adapters/__init__.py`
- Create: `core25/adapters/core20.py`
- Create: `core25/requirement_engine.py`
- Test: `tests/core25/test_core20_adapter.py`

**Interfaces:**
- `adapt_requirement(req: core20.model.Requirement) -> Requirement25`
- `adapt_evidence(ev: core20.model.Evidence) -> Evidence25`
- `normalize_assignment_requirement(raw: dict) -> Requirement25`
- Must preserve stable source identity and page/fragment provenance.

- [ ] **Step 1: Write failing adapter tests**

```python
from core20.model import Evidence, Requirement
from core25.adapters.core20 import adapt_evidence, adapt_requirement
from core25.contracts import Domain, Scope


def test_core20_assignment_requirement_preserves_route_and_scope():
    old = Requirement(
        requirement_id="A-12",
        domain="assignment",
        text="Продолжительность смены – 12 часов",
        expected_parameter_code="SHIFT_DURATION",
        expected_evidence_route=["ТХ"],
        verification_kind="VALUE",
        metadata={"required_value": 12.0, "unit": "час", "scope": "PROJECT_GLOBAL"},
    )
    new = adapt_requirement(old)
    assert new.requirement_id == "A-12"
    assert new.domain is Domain.ASSIGNMENT
    assert new.scope is Scope.PROJECT_GLOBAL
    assert new.parameter_code == "SHIFT_DURATION"
    assert new.expected_sections == ("ТХ",)


def test_core20_evidence_keeps_canonical_address():
    old = Evidence(evidence_id="E1", document_name="ТХ.pdf", section="ТХ", page=7, fragment="Продолжительность смены 12 часов", addressable=True, trusted=True)
    new = adapt_evidence(old)
    assert new.document == "ТХ.pdf"
    assert new.page == 7
    assert new.fragment.startswith("Продолжительность")
    assert new.addressable is True
```

- [ ] **Step 2: Run RED**

Run: `pytest tests/core25/test_core20_adapter.py -v`

Expected: missing adapter functions.

- [ ] **Step 3: Implement adapters without changing core20**

Mapping rules:
- domain `assignment` / `задание на проектирование` → `Domain.ASSIGNMENT`;
- metadata scope `PROJECT_GLOBAL` → `Scope.PROJECT_GLOBAL`; any explicit target object or equipment/object verification kind → `Scope.OBJECT_SPECIFIC`; otherwise `Scope.UNRESOLVED`;
- `expected_evidence_route` → tuple `expected_sections`;
- `expected_parameter_code` → uppercase `parameter_code`;
- evidence `document_name or document_id`, `section`, `page`, `fragment`, `addressable`, `trusted`, `metadata` copied exactly.

- [ ] **Step 4: Run GREEN plus legacy evidence tests**

Run:
`pytest tests/core25/test_core20_adapter.py test_evidence_driven_requirements_100.py -v`

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add core25/adapters core25/requirement_engine.py tests/core25/test_core20_adapter.py
git commit -m "feat(core25): adapt stable core20 requirements and evidence"
```

---

### Task 3: Requirement routing contracts

**Files:**
- Create: `core25/routing.py`
- Test: `tests/core25/test_requirement_routing.py`

**Interfaces:**
- `VerificationRoute` dataclass with `kind`, `scope`, `expected_sections`, `parameter_code`, `requires_owner`, `requires_addressable_evidence`.
- `route_requirement(requirement: Requirement25) -> VerificationRoute`.

- [ ] **Step 1: Write failing routing tests**

```python
from core25.contracts import Domain, Requirement25, Scope
from core25.routing import route_requirement


def test_project_global_numeric_route_does_not_require_owner():
    req = Requirement25(requirement_id="A1", domain=Domain.ASSIGNMENT, text="Продолжительность смены 12 часов", scope=Scope.PROJECT_GLOBAL, verification_kind="TYPED_VALUE", parameter_code="SHIFT_DURATION", required_value=12.0, unit="час", expected_sections=("ТХ",))
    route = route_requirement(req)
    assert route.requires_owner is False
    assert route.parameter_code == "SHIFT_DURATION"


def test_object_specific_numeric_route_requires_owner():
    req = Requirement25(requirement_id="A2", domain=Domain.ASSIGNMENT, text="Автосамосвал объем кузова 32 м3", scope=Scope.OBJECT_SPECIFIC, verification_kind="TYPED_VALUE", parameter_code="BODY_VOLUME", target_object_id="TRUCK-1", required_value=32.0, unit="м3", expected_sections=("ТХ",))
    route = route_requirement(req)
    assert route.requires_owner is True


def test_unsupported_semantic_requirement_routes_to_review_kind():
    req = Requirement25(requirement_id="A3", domain=Domain.ASSIGNMENT, text="Обеспечить удобство эксплуатации", scope=Scope.UNRESOLVED, verification_kind="SEMANTIC_UNSUPPORTED")
    assert route_requirement(req).kind == "REVIEW_ONLY"
```

- [ ] **Step 2: Run RED**

Run: `pytest tests/core25/test_requirement_routing.py -v`

Expected: `core25.routing` missing.

- [ ] **Step 3: Implement route selection**

Supported Alpha 1 kinds map as follows:
- `TYPED_VALUE` → `TYPED_VALUE`;
- `PRESENCE` → `PRESENCE`;
- `RESERVE_TOPOLOGY` → `RESERVE_TOPOLOGY`;
- `TABLE_CELL_VALUE` → `TYPED_VALUE` with structured source preference;
- anything else → `REVIEW_ONLY`.

`requires_addressable_evidence=True` for every route except `REVIEW_ONLY`.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/core25/test_requirement_routing.py -v`

- [ ] **Step 5: Commit**

```bash
git add core25/routing.py tests/core25/test_requirement_routing.py
git commit -m "feat(core25): add explicit requirement routing contracts"
```

---

### Task 4: Canonical evidence qualification gate

**Files:**
- Create: `core25/evidence.py`
- Test: `tests/core25/test_evidence_gate.py`

**Interfaces:**
- `is_canonical_evidence(ev: Evidence25) -> bool`
- `qualify_evidence(candidates: list[Evidence25], route: VerificationRoute) -> tuple[Evidence25, ...]`

- [ ] **Step 1: Write failing evidence tests**

```python
from core25.contracts import Evidence25
from core25.evidence import is_canonical_evidence


def test_table_of_contents_entry_is_rejected_even_when_addressable():
    ev = Evidence25(evidence_id="TOC", document="ПЗ.pdf", page=2, fragment="5 Технологические решения ........ 45", addressable=True, source_kind="TABLE_OF_CONTENTS")
    assert is_canonical_evidence(ev) is False


def test_real_page_fragment_is_canonical():
    ev = Evidence25(evidence_id="E1", document="ТХ.pdf", page=18, fragment="Производительность дробилки составляет 500 т/ч.", addressable=True, source_kind="PAGE_TEXT")
    assert is_canonical_evidence(ev) is True


def test_unaddressable_semantic_hit_is_rejected():
    ev = Evidence25(evidence_id="SEM", document="ТХ.pdf", page=None, fragment="500 т/ч", addressable=False, source_kind="SEMANTIC_SEARCH")
    assert is_canonical_evidence(ev) is False
```

- [ ] **Step 2: Run RED**

Run: `pytest tests/core25/test_evidence_gate.py -v`

- [ ] **Step 3: Implement fail-closed evidence gate**

Reject when any of these is true:
- `addressable` false;
- document empty;
- page is not positive integer;
- fragment empty;
- source kind in `{TABLE_OF_CONTENTS, INDEX, DOCUMENT_TITLE, FILE_NAME_ONLY}`;
- metadata `is_toc`, `is_index`, or `heading_only` is true;
- fragment normalizes to only a section/index line without a project assertion.

Do not reject merely because `trusted=False`; trust affects later proof strength, not addressability.

- [ ] **Step 4: Run GREEN**

Run: `pytest tests/core25/test_evidence_gate.py -v`

- [ ] **Step 5: Commit**

```bash
git add core25/evidence.py tests/core25/test_evidence_gate.py
git commit -m "feat(core25): enforce canonical evidence gate"
```

---

### Task 5: First-class owner and parameter binding

**Files:**
- Create: `core25/binding.py`
- Test: `tests/core25/test_binding.py`

**Interfaces:**
- `bind_evidence(requirement: Requirement25, evidence: Evidence25, known_objects: dict[str, tuple[str, ...]]) -> Binding25`
- Binding result records `owner_id`, `parameter_code`, `state`, `method`, `reason`.

- [ ] **Step 1: Write failing binding tests**

```python
from core25.binding import bind_evidence
from core25.contracts import BindingState, Domain, Evidence25, Requirement25, Scope


def test_wrong_owner_cannot_bind_same_parameter():
    req = Requirement25(requirement_id="R1", domain=Domain.ASSIGNMENT, text="Площадь здания проборазделки 89,9 м2", scope=Scope.OBJECT_SPECIFIC, target_object_id="OBJ-LAB", verification_kind="TYPED_VALUE", parameter_code="AREA")
    ev = Evidence25(evidence_id="E1", document="АР.pdf", page=12, fragment="Модуль обеспыливания. Площадь 23,5 м2", addressable=True, metadata={"owner_name": "Модуль обеспыливания", "parameter_code": "AREA"})
    result = bind_evidence(req, ev, {"OBJ-LAB": ("здание проборазделки",), "OBJ-DUST": ("модуль обеспыливания",)})
    assert result.state is BindingState.REJECTED
    assert result.owner_id == "OBJ-DUST"


def test_project_global_value_can_bind_without_owner():
    req = Requirement25(requirement_id="R2", domain=Domain.ASSIGNMENT, text="Продолжительность смены 12 часов", scope=Scope.PROJECT_GLOBAL, verification_kind="TYPED_VALUE", parameter_code="SHIFT_DURATION")
    ev = Evidence25(evidence_id="E2", document="ТХ.pdf", page=7, fragment="Продолжительность смены составляет 12 часов", addressable=True, metadata={"parameter_code": "SHIFT_DURATION"})
    result = bind_evidence(req, ev, {})
    assert result.state is BindingState.BOUND
    assert result.owner_id == "PROJECT"
```

- [ ] **Step 2: Run RED**

Run: `pytest tests/core25/test_binding.py -v`

- [ ] **Step 3: Implement deterministic binding order**

Binding precedence:
1. explicit structured `owner_id`/`owner_name` + parameter metadata;
2. exact known object alias in structured row/cell context;
3. project-global contract → owner `PROJECT`;
4. semantic owner hints may produce `AMBIGUOUS` but never `BOUND` unless corroborated by structured owner evidence;
5. conflicting explicit owner → `REJECTED`;
6. no owner proof for object-specific requirement → `UNBOUND`.

Parameter mismatch always yields `REJECTED`, even if owner matches.

- [ ] **Step 4: Run GREEN and legacy owner regression**

Run:
`pytest tests/core25/test_binding.py test_evidence_driven_requirements_100.py test_evidence_provenance_96.py -v`

- [ ] **Step 5: Commit**

```bash
git add core25/binding.py tests/core25/test_binding.py
git commit -m "feat(core25): add first-class owner and parameter binding"
```

---

### Task 6: Proof assembly and strict decision mapping

**Files:**
- Create: `core25/proof.py`
- Create: `core25/decision.py`
- Test: `tests/core25/test_proof_decision.py`

**Interfaces:**
- `build_proof(requirement, route, evidence, bindings) -> Proof25`
- `decide(proof: Proof25) -> Decision25`

- [ ] **Step 1: Write failing proof tests**

```python
from core25.contracts import Binding25, BindingState, DecisionState, Evidence25, ProofState
from core25.decision import decide
from core25.proof import build_proof


def test_positive_semantic_judgment_without_selected_evidence_stays_insufficient(requirement_factory, route_factory):
    req = requirement_factory(metadata={"judge_verdict": "SUPPORTS", "critic_accept": True})
    proof = build_proof(req, route_factory(), (), ())
    assert proof.state is ProofState.INSUFFICIENT
    assert decide(proof).state is DecisionState.REVIEW


def test_bound_typed_value_match_is_proven(requirement_factory, route_factory):
    req = requirement_factory(required_value=12.0, unit="час", parameter_code="SHIFT_DURATION")
    ev = Evidence25(evidence_id="E1", document="ТХ.pdf", page=7, fragment="Продолжительность смены 12 часов", addressable=True, metadata={"value": 12.0, "unit": "час", "parameter_code": "SHIFT_DURATION"})
    binding = Binding25(binding_id="B1", evidence_id="E1", state=BindingState.BOUND, owner_id="PROJECT", parameter_code="SHIFT_DURATION")
    proof = build_proof(req, route_factory(parameter_code="SHIFT_DURATION"), (ev,), (binding,))
    assert proof.state is ProofState.PROVEN_MATCH
    assert decide(proof).state is DecisionState.COMPLIANT
```

Add local fixtures in the same test module; do not introduce global fixtures for two small constructors.

- [ ] **Step 2: Run RED**

Run: `pytest tests/core25/test_proof_decision.py -v`

- [ ] **Step 3: Implement proof plugins behind one dispatcher**

Dispatcher handles:
- typed numeric value using normalized units and existing `core20.parameter_contracts.compare_values` through adapter wrapper;
- presence requiring a bound canonical fragment with a project assertion marker;
- reserve topology using stable 20.0 parser through adapter;
- `REVIEW_ONLY` → `INSUFFICIENT`;
- conflicting same-owner typed values → `CONFLICT`.

Before any plugin runs, remove evidence whose binding state is not `BOUND`. If no bound canonical evidence remains, return `INSUFFICIENT`.

Decision mapping:
- `PROVEN_MATCH` → `COMPLIANT`;
- `PROVEN_MISMATCH` → `NONCOMPLIANT`;
- `NOT_APPLICABLE` → `NOT_APPLICABLE`;
- `SYSTEM_LIMITATION` → `LIMITATION`;
- `CONFLICT` or `INSUFFICIENT` → `REVIEW`.

- [ ] **Step 4: Run GREEN plus semantic proof regression**

Run:
`pytest tests/core25/test_proof_decision.py test_core20_alpha1013_proof_trace.py -v`

- [ ] **Step 5: Commit**

```bash
git add core25/proof.py core25/decision.py tests/core25/test_proof_decision.py
git commit -m "feat(core25): add deterministic proof and decision gates"
```

---

### Task 7: End-to-end Assignment pipeline

**Files:**
- Create: `core25/pipeline.py`
- Modify: `core25/__init__.py`
- Test: `tests/core25/test_assignment_pipeline.py`

**Interfaces:**
- `verify_assignment(requirements, evidence, known_objects) -> tuple[VerificationResult25, ...]`
- Public import: `from core25 import verify_assignment`.

- [ ] **Step 1: Write failing end-to-end tests**

```python
from core25 import verify_assignment
from core25.contracts import DecisionState


def test_pipeline_rejects_wrong_owner_and_does_not_create_mismatch(sample_assignment_requirements, sample_evidence, sample_objects):
    results = verify_assignment(sample_assignment_requirements, sample_evidence, sample_objects)
    area = next(x for x in results if x.requirement.requirement_id == "AREA-LAB")
    assert area.decision.state is DecisionState.REVIEW
    assert all(b.owner_id != "OBJ-LAB" or b.state.value != "BOUND" for b in area.trace.bindings)


def test_pipeline_traces_categorical_result_to_document_page_fragment(sample_assignment_requirements, sample_evidence, sample_objects):
    results = verify_assignment(sample_assignment_requirements, sample_evidence, sample_objects)
    shift = next(x for x in results if x.requirement.requirement_id == "SHIFT")
    assert shift.decision.state is DecisionState.COMPLIANT
    assert shift.trace.is_categorical_trace_valid() is True
    assert shift.trace.evidence[0].document == "ТХ.pdf"
    assert shift.trace.evidence[0].page == 7
```

Test fixture must include at least:
- project-global shift duration 12 h;
- object-specific building area 89.9 m²;
- wrong-owner dust-module area 23.5 m²;
- one unsupported semantic requirement.

- [ ] **Step 2: Run RED**

Run: `pytest tests/core25/test_assignment_pipeline.py -v`

- [ ] **Step 3: Implement orchestration only**

For each requirement:
1. normalize/adapt;
2. route;
3. qualify evidence by expected sections and canonical evidence gate;
4. bind each qualified candidate;
5. build proof;
6. map decision;
7. create trace;
8. construct `VerificationResult25`.

No domain-specific verification logic may be placed in `pipeline.py`.

- [ ] **Step 4: Run GREEN and focused 20.0 suite**

Run:
`pytest tests/core25/test_assignment_pipeline.py test_evidence_driven_requirements_100.py test_core20_alpha1012_evidence_quality.py test_core20_alpha1013_proof_trace.py -v`

- [ ] **Step 5: Commit**

```bash
git add core25/pipeline.py core25/__init__.py tests/core25/test_assignment_pipeline.py
git commit -m "feat(core25): add unified assignment verification pipeline"
```

---

### Task 8: Test 78 Golden Set automation

**Files:**
- Create: `core25/golden/test78_cases.json`
- Create: `tests/core25/test_golden_test78.py`

**Interfaces:**
- Golden JSON schema fields: `case_id`, `defect_class`, `requirement`, `evidence`, `objects`, `expected_decision`, `expected_proof_state`, `forbidden_evidence_ids`.
- Test loads cases and sends them through `verify_assignment` or lower-level gate where the defect is domain-independent.

- [ ] **Step 1: Add Golden cases and failing parameterized test**

Initial cases must cover exactly these defect classes:
1. `toc_as_evidence`;
2. `wrong_object_owner`;
3. `wrong_semantic_parameter`;
4. `owner_section_absent`;
5. `judge_critic_without_canonical_proof`;
6. `provider_429_not_success`;
7. `nan_value_rejected`;
8. `canonical_proof_trace_required`;
9. `positive_semantic_without_selected_evidence`.

Parameterized assertion:

```python
@pytest.mark.parametrize("case", load_cases(), ids=lambda x: x["case_id"])
def test_test78_golden_case(case):
    result = run_case(case)
    assert result.decision.state.value == case["expected_decision"]
    assert result.proof.state.value == case["expected_proof_state"]
    used = set(result.proof.evidence_ids)
    assert used.isdisjoint(case.get("forbidden_evidence_ids", []))
```

- [ ] **Step 2: Run RED**

Run: `pytest tests/core25/test_golden_test78.py -v`

Expected: at least provider/NaN/persistence-related cases fail until explicit normalization is implemented.

- [ ] **Step 3: Add only minimal normalization required by Golden cases**

Rules:
- non-finite numeric values (`nan`, `inf`, `-inf`) cannot become typed facts;
- provider error metadata (`429`, timeout, unavailable) returns `SYSTEM_LIMITATION` or `INSUFFICIENT`, never proof match;
- Judge/Critic metadata never creates evidence;
- evidence id listed as forbidden must never appear in proof.

- [ ] **Step 4: Run Golden Set GREEN plus all core25 tests**

Run: `pytest tests/core25 -v`

- [ ] **Step 5: Commit**

```bash
git add core25/golden tests/core25/test_golden_test78.py core25
git commit -m "test(core25): automate Test 78 golden regressions"
```

---

### Task 9: Persistence, report trace, and Alpha 1 acceptance gate

**Files:**
- Create: `core25/persistence.py`
- Create: `core25/report_trace.py`
- Test: `tests/core25/test_persistence_report_trace.py`

**Interfaces:**
- `dump_results(results: tuple[VerificationResult25, ...]) -> str`
- `load_results(payload: str) -> tuple[VerificationResult25, ...]`
- `report_row(result: VerificationResult25) -> dict[str, object]`

- [ ] **Step 1: Write failing persistence/report tests**

```python
from core25.persistence import dump_results, load_results
from core25.report_trace import report_row


def test_roundtrip_preserves_canonical_trace(categorical_result):
    restored = load_results(dump_results((categorical_result,)))[0]
    assert restored.trace.is_categorical_trace_valid() is True
    assert restored.trace.proof.evidence_ids == categorical_result.trace.proof.evidence_ids


def test_report_row_contains_clickable_trace_fields_and_no_nan(categorical_result):
    row = report_row(categorical_result)
    assert row["document"]
    assert isinstance(row["page"], int)
    assert row["fragment"]
    assert "nan" not in str(row).casefold()
    assert "alpha 9" not in str(row).casefold()
```

- [ ] **Step 2: Run RED**

Run: `pytest tests/core25/test_persistence_report_trace.py -v`

- [ ] **Step 3: Implement deterministic JSON roundtrip and report-safe mapping**

Persistence must serialize enum values and nested dataclasses explicitly; loader reconstructs exact contract types rather than returning raw dictionaries.

`report_row` exposes:
- `requirement_id`;
- `decision`;
- `reason`;
- `document`;
- `page`;
- `fragment`;
- `evidence_id`;
- `binding_id`;
- `proof_id`.

For `REVIEW/LIMITATION`, document/page/fragment may be empty. For categorical decisions, missing trace raises `ValueError` instead of silently exporting a categorical row.

- [ ] **Step 4: Run complete Alpha 1 verification suite**

Run:
```bash
pytest tests/core25 -v
pytest test_evidence_driven_requirements_100.py test_evidence_provenance_96.py test_core20_alpha1012_evidence_quality.py test_core20_alpha1013_proof_trace.py -v
pytest -q
python -m compileall core25
```

Expected:
- all `tests/core25` green;
- focused 20.0 regressions green;
- full repository suite green except only previously documented fixture-dependent skips, never new failures;
- compileall success.

- [ ] **Step 5: Add Alpha 1 acceptance assertion test**

In `tests/core25/test_assignment_pipeline.py`, add a control-package test that loads/imports the known 56 Assignment requirements fixture available to the existing test environment and asserts:

```python
assert len(results) == 56
assert all(r.route.kind for r in results)
assert all(r.requirement.scope.value for r in results)
for result in results:
    if result.decision.state.value in {"COMPLIANT", "NONCOMPLIANT"}:
        assert result.trace.is_categorical_trace_valid()
```

If the 56-requirement external PDF fixture is unavailable in CI, use the repository's already materialized structured requirement fixture rather than skipping this gate.

- [ ] **Step 6: Commit**

```bash
git add core25/persistence.py core25/report_trace.py tests/core25
git commit -m "feat(core25): preserve proof trace through persistence and reports"
```

---

## Final self-review checklist

Before declaring Alpha 1 implementation complete:

1. Confirm every spec acceptance gate maps to at least one automated test above.
2. Search the new code for `TODO`, `TBD`, `pass`, unconditional `COMPLIANT`, unconditional `NONCOMPLIANT`, and raw `float('nan')` propagation.
3. Confirm no `core20` production file changed; if one changed, review it separately and justify the necessity in the commit message.
4. Confirm `tests/core25/test_golden_test78.py` includes every required initial defect class.
5. Confirm the known wrong-owner 89.9 m² versus 23.5 m² case cannot produce `NONCOMPLIANT`.
6. Confirm a positive Judge/Critic result without selected addressable evidence remains `REVIEW`.
7. Confirm categorical report rows contain document, page, fragment, evidence id, binding id, and proof id.
8. Confirm full repository pytest introduces zero new failures.

## Release criterion

Do not name the build `25.0 Alpha 1` merely because code exists. The release name is earned only after all Task 9 commands are green and all design acceptance gates are satisfied. The quality KPI is proof precision: fewer honest automatic decisions are preferable to more weak categorical decisions.
