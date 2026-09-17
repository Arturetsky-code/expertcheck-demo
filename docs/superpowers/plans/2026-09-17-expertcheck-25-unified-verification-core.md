# ExpertCheck 25.0 Alpha 1 — Unified Verification Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first `core25` vertical slice so every Design Assignment requirement follows one auditable `Requirement → Route → Evidence → Binding → Proof → Decision → Trace` pipeline.

**Architecture:** Add `core25` beside stable `core20`. Reuse proven `core20` parameter/proof helpers only through explicit adapters; all 25.0 categorical decisions are owned by new fail-closed integrity gates. Alpha 1 covers Design Assignment first and converts Test 78 defects into automated Golden Set regressions.

**Tech Stack:** Python 3, dataclasses/enums, pytest, existing ExpertCheck `core20` canonical model and regression fixtures.

**Spec:** `docs/superpowers/specs/2026-09-17-expertcheck-25-quality-leap-design.md`

## Global Constraints

- Stable baseline: `6afaf020f329f07bdbce6d0ea2c0e1238023aed6`.
- Implementation branch: `codex/expertcheck-25.0-quality-leap`.
- No production code before a failing test.
- `core20` remains the stable control implementation.
- No `COMPLIANT`/`NONCOMPLIANT` without addressable canonical evidence.
- Wrong owner or wrong semantic parameter must fail closed.
- TOC/index/title-only evidence can never satisfy proof.
- AI/Judge/Critic cannot independently create categorical proof.
- Provider 429/timeout/failure cannot be recorded as successful verification.
- Every categorical decision must trace to evidence document + page + fragment.
- Existing `core20` regressions remain mandatory.

---

### Task 1: Core 25 contracts and integrity states

**Files:**
- Create: `core25/__init__.py`
- Create: `core25/contracts.py`
- Test: `tests/core25/test_contracts.py`

**Interfaces:**
- Produces enums: `Domain`, `Scope`, `BindingState`, `ProofState`, `DecisionState`.
- Produces dataclasses: `Requirement25`, `Route25`, `Evidence25`, `Binding25`, `Proof25`, `Decision25`, `Trace25`.
- Produces `stable_id(prefix: str, *parts: object) -> str`.

- [ ] **Step 1: Write failing tests**

```python
from core25.contracts import Decision25, DecisionState, Evidence25, Proof25, ProofState


def test_noncanonical_evidence_is_not_proof_eligible():
    e = Evidence25(
        evidence_id="E1", document_name="ПЗ.pdf", page=2,
        fragment="Оглавление", addressable=True, canonical=False,
        source_role="TOC",
    )
    assert e.proof_eligible is False


def test_categorical_states_are_explicit():
    p = Proof25(proof_id="P1", requirement_id="R1", state=ProofState.PROVEN_MATCH)
    d = Decision25(decision_id="D1", requirement_id="R1", state=DecisionState.COMPLIANT, proof_id="P1", trace_id="T1")
    assert p.is_categorical is True
    assert d.is_categorical is True
```

- [ ] **Step 2: Verify RED**

Run: `pytest -q tests/core25/test_contracts.py`

Expected: import failure because `core25` does not yet exist.

- [ ] **Step 3: Implement minimal contracts**

`Evidence25.proof_eligible` is true only if `addressable`, `canonical`, fragment is non-empty, page is present, and `source_role` is not `TOC`, `INDEX`, or `TITLE_ONLY`. `Proof25.is_categorical` is true only for `PROVEN_MATCH`/`PROVEN_MISMATCH`; `Decision25.is_categorical` only for `COMPLIANT`/`NONCOMPLIANT`.

- [ ] **Step 4: Verify GREEN**

Run: `pytest -q tests/core25/test_contracts.py`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add core25 tests/core25/test_contracts.py
git commit -m "feat(core25): add unified verification contracts"
```

---

### Task 2: Core20 adapter and Assignment requirement normalization

**Files:**
- Create: `core25/adapters/__init__.py`
- Create: `core25/adapters/core20.py`
- Create: `core25/requirement_engine.py`
- Test: `tests/core25/test_requirement_engine.py`

**Interfaces:**
- Produces `adapt_requirement(source: object) -> Requirement25`.
- Produces `normalize_assignment_requirements(rows: list[object]) -> list[Requirement25]`.

- [ ] **Step 1: Write failing tests**

```python
from core25.requirement_engine import normalize_assignment_requirements


def test_requirement_source_address_is_preserved():
    req = normalize_assignment_requirements([{
        "requirement_id": "A15",
        "requirement_text": "Продолжительность смены – 12 часов",
        "parameter_code": "SHIFT_DURATION",
        "required_value": 12.0,
        "unit": "часов",
        "source_document": "ЗНП.pdf",
        "source_page": 4,
        "source_row": "15",
    }])[0]
    assert req.requirement_id == "A15"
    assert req.source_document == "ЗНП.pdf"
    assert req.source_page == 4
    assert req.source_row == "15"
    assert req.expected_parameter_code == "SHIFT_DURATION"


def test_missing_legacy_id_gets_deterministic_id():
    row = {"requirement_text": "Предусмотреть ограждение площадки", "source_row": "31"}
    a = normalize_assignment_requirements([row])[0]
    b = normalize_assignment_requirements([row])[0]
    assert a.requirement_id == b.requirement_id
    assert a.requirement_id.startswith("REQ25-")
```

- [ ] **Step 2: Verify RED**

Run: `pytest -q tests/core25/test_requirement_engine.py`

Expected: missing module/function.

- [ ] **Step 3: Implement minimal adapter and normalizer**

Support dict-style legacy rows and `core20.model.Requirement`. Never mutate source objects and never import verdicts from 20.0. Missing IDs use `stable_id("REQ25", source_document, source_page, source_row, text)`.

- [ ] **Step 4: Verify GREEN + legacy requirement regression**

Run:
```bash
pytest -q tests/core25/test_requirement_engine.py test_evidence_driven_requirements_100.py test_assignment_checklist_automation_93.py
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add core25/adapters core25/requirement_engine.py tests/core25/test_requirement_engine.py
git commit -m "feat(core25): normalize assignment requirements"
```

---

### Task 3: Explicit requirement routing contracts

**Files:**
- Create: `core25/routing.py`
- Test: `tests/core25/test_routing.py`

**Interfaces:**
- Produces `route_requirement(requirement: Requirement25) -> Route25`.
- Alpha 1 verification kinds: `TYPED_VALUE`, `PROJECT_GLOBAL_VALUE`, `PRESENCE`, `EQUIPMENT_TOPOLOGY`, `STRUCTURED_CELL`, `SEMANTIC_REVIEW`.

- [ ] **Step 1: Write failing tests**

```python
from core25.contracts import Requirement25, Scope
from core25.routing import route_requirement


def test_shift_duration_is_project_global():
    req = Requirement25(
        requirement_id="A1", domain="ASSIGNMENT",
        text="Продолжительность смены – 12 часов",
        expected_parameter_code="SHIFT_DURATION", required_value=12.0, required_unit="часов",
    )
    route = route_requirement(req)
    assert route.scope is Scope.PROJECT_GLOBAL
    assert route.verification_kind == "PROJECT_GLOBAL_VALUE"


def test_equipment_value_requires_owner():
    req = Requirement25(
        requirement_id="A2", domain="ASSIGNMENT",
        text="Автосамосвал SinoTrack объемом кузова 32 м3",
        target_object_name="Автосамосвал SinoTrack",
        expected_parameter_code="BODY_VOLUME", required_value=32.0, required_unit="м3",
    )
    route = route_requirement(req)
    assert route.scope is Scope.OBJECT
    assert route.require_owner is True
    assert route.verification_kind == "TYPED_VALUE"


def test_unsupported_semantic_requirement_fails_to_review_route():
    req = Requirement25(requirement_id="A3", domain="ASSIGNMENT", text="Обеспечить безопасную эксплуатацию объекта")
    route = route_requirement(req)
    assert route.verification_kind == "SEMANTIC_REVIEW"
    assert route.categorical_allowed is False
```

- [ ] **Step 2: Verify RED**

Run: `pytest -q tests/core25/test_routing.py`

Expected: missing router.

- [ ] **Step 3: Implement deterministic routing**

Use `core20.parameter_contracts.canonical_contract` only through `core25/adapters/core20.py`. Project-global codes explicitly include `SHIFT_DURATION`. Unknown semantic requirements route to `SEMANTIC_REVIEW`; they are never guessed into a numeric/presence check.

- [ ] **Step 4: Verify GREEN**

Run: `pytest -q tests/core25/test_routing.py test_evidence_driven_requirements_100.py`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add core25/routing.py tests/core25/test_routing.py
git commit -m "feat(core25): add assignment verification routing"
```

---

### Task 4: Canonical evidence qualification

**Files:**
- Create: `core25/evidence.py`
- Modify: `core25/adapters/core20.py`
- Test: `tests/core25/test_evidence.py`

**Interfaces:**
- Produces `collect_evidence(requirement, route, page_corpus) -> list[Evidence25]`.

- [ ] **Step 1: Write failing TOC regression**

```python
from core25.evidence import collect_evidence
from core25.requirement_engine import normalize_assignment_requirements
from core25.routing import route_requirement


def test_toc_hit_is_not_proof_eligible_but_real_page_is():
    req = normalize_assignment_requirements([{"requirement_text": "Предусмотреть ограждение площадки", "source_row": "31"}])[0]
    route = route_requirement(req)
    corpus = [
        {"document": "ПЗ.pdf", "document_type": "ПЗ", "page": 2, "text": "ОГЛАВЛЕНИЕ\n5 Ограждение площадки .... 41"},
        {"document": "ПЗУ.pdf", "document_type": "ПЗУ", "page": 41, "text": "По периметру площадки предусмотрено металлическое ограждение."},
    ]
    evidence = collect_evidence(req, route, corpus)
    assert next(x for x in evidence if x.page == 2).proof_eligible is False
    assert next(x for x in evidence if x.page == 41).proof_eligible is True
```

- [ ] **Step 2: Verify RED**

Run: `pytest -q tests/core25/test_evidence.py`

Expected: collector missing.

- [ ] **Step 3: Implement canonical qualification**

Translate page corpus rows into `Evidence25`. Detect TOC/index using heading markers plus dotted-leader/page-number patterns. Preserve rejected evidence for diagnostics, but set `canonical=False`, `source_role="TOC"`. Require page + fragment for proof eligibility.

- [ ] **Step 4: Verify GREEN + Alpha 10.1.3 proof regression**

Run:
```bash
pytest -q tests/core25/test_evidence.py test_core20_alpha1012_evidence_quality.py test_core20_alpha1013_proof_trace.py
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add core25/evidence.py core25/adapters/core20.py tests/core25/test_evidence.py
git commit -m "feat(core25): qualify canonical evidence"
```

---

### Task 5: First-class owner and parameter binding

**Files:**
- Create: `core25/binding.py`
- Test: `tests/core25/test_binding.py`

**Interfaces:**
- Produces `bind_evidence(requirement, route, evidence) -> Binding25`.

- [ ] **Step 1: Write failing wrong-owner regression**

```python
from core25.binding import bind_evidence
from core25.contracts import BindingState, Evidence25, Requirement25
from core25.routing import route_requirement


def test_probe_building_area_cannot_bind_to_dust_module_area():
    req = Requirement25(
        requirement_id="AREA1", domain="ASSIGNMENT",
        text="Здание проборазделки общей площадью 89,9 м2",
        target_object_name="Здание проборазделки",
        expected_parameter_code="AREA_TOTAL", required_value=89.9, required_unit="м2",
    )
    evidence = Evidence25(
        evidence_id="E1", document_name="АР.pdf", section="АР", page=12,
        fragment="Модуль обеспыливания. Общая площадь 23,5 м2.",
        addressable=True, canonical=True,
    )
    binding = bind_evidence(req, route_requirement(req), evidence)
    assert binding.state in {BindingState.UNBOUND, BindingState.REJECTED}
    assert binding.owner_match is False
```

- [ ] **Step 2: Verify RED**

Run: `pytest -q tests/core25/test_binding.py`

Expected: binding module missing.

- [ ] **Step 3: Implement binding gate**

Compute owner match and parameter/concept match separately. For object-specific routes, parameter match without owner match is `REJECTED`. Project-global routes may bypass owner only because `Route25.scope == PROJECT_GLOBAL`, never because owner extraction failed.

- [ ] **Step 4: Verify GREEN + historical binding regressions**

Run:
```bash
pytest -q tests/core25/test_binding.py test_evidence_provenance_96.py test_binding_integrity_risk_hotfix_9512.py test_object_tep_binding.py
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add core25/binding.py tests/core25/test_binding.py
git commit -m "feat(core25): add strict evidence binding"
```

---

### Task 6: Canonical proof and fail-closed decision machine

**Files:**
- Create: `core25/proof.py`
- Create: `core25/decision.py`
- Test: `tests/core25/test_proof_decision.py`

**Interfaces:**
- Produces `build_proof(requirement, route, evidence, bindings, ai_support=None) -> Proof25`.
- Produces `decide(requirement, proof) -> Decision25`.

- [ ] **Step 1: Write failing proof tests**

```python
from core25.contracts import DecisionState, ProofState
from core25.decision import decide
from core25.proof import build_proof


def test_ai_consensus_without_selected_canonical_evidence_is_insufficient(sample_requirement, sample_route):
    proof = build_proof(sample_requirement, sample_route, [], [], ai_support={"judge_verdict": "SUPPORTS", "critic_accept": True})
    assert proof.state is ProofState.INSUFFICIENT
    assert decide(sample_requirement, proof).state is DecisionState.REVIEW
```

Fixtures in this test file must instantiate real core25 contracts; no mocks of proof/decision functions.

- [ ] **Step 2: Verify RED**

Run: `pytest -q tests/core25/test_proof_decision.py`

Expected: modules missing.

- [ ] **Step 3: Implement proof gates**

Only `BOUND` + proof-eligible evidence may participate. For typed values, reuse numeric/unit extraction through the adapter. Conflicting bound values yield `CONFLICT`. `PROVEN_MATCH`/`PROVEN_MISMATCH` require evidence IDs and binding IDs. Map only `PROVEN_MATCH → COMPLIANT` and `PROVEN_MISMATCH → NONCOMPLIANT`; other states map to `REVIEW`, `LIMITATION`, or `NOT_APPLICABLE`.

- [ ] **Step 4: Verify GREEN + semantic proof regression**

Run:
```bash
pytest -q tests/core25/test_proof_decision.py test_core20_alpha1013_proof_trace.py test_trust_pipeline_100a5.py
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add core25/proof.py core25/decision.py tests/core25/test_proof_decision.py
git commit -m "feat(core25): add canonical proof decision gates"
```

---

### Task 7: Complete Assignment vertical pipeline and 56/56 structural gate

**Files:**
- Create: `core25/pipeline.py`
- Modify: `core25/__init__.py`
- Test: `tests/core25/test_assignment_pipeline.py`

**Interfaces:**
- Produces `verify_assignment(requirement_rows, page_corpus, ai_context=None) -> AssignmentRun25`.
- `AssignmentRun25` exposes dictionaries for requirements, routes, evidence, bindings, proofs, decisions, traces, plus counts.

- [ ] **Step 1: Write failing end-to-end test**

```python
from core25.pipeline import verify_assignment


def test_assignment_result_is_traceable_to_document_page_fragment():
    requirements = [{
        "requirement_id": "A15", "requirement_text": "Продолжительность смены – 12 часов",
        "parameter_code": "SHIFT_DURATION", "required_value": 12.0, "unit": "часов",
    }]
    corpus = [{
        "document": "ТХ.pdf", "document_type": "ТХ", "page": 7,
        "text": "Проектом принят режим работы. Продолжительность смены составляет 12 часов.",
    }]
    run = verify_assignment(requirements, corpus)
    decision = run.decisions["A15"]
    assert decision.state.value == "COMPLIANT"
    trace = run.traces[decision.trace_id]
    proof = run.proofs[trace.proof_id]
    evidence = run.evidence[proof.evidence_ids[0]]
    assert evidence.document_name == "ТХ.pdf"
    assert evidence.page == 7
    assert "12 часов" in evidence.fragment
```

- [ ] **Step 2: Verify RED**

Run: `pytest -q tests/core25/test_assignment_pipeline.py`

Expected: pipeline missing.

- [ ] **Step 3: Implement orchestration only**

`pipeline.py` composes requirement normalization, routing, evidence, binding, proof, and decision. It must not duplicate those rules. Every requirement gets a route, trace, and terminal decision even when that decision is `REVIEW`/`LIMITATION`.

- [ ] **Step 4: Add 56/56 structural acceptance test**

Use the already committed 56 atomic requirement rows from the existing Assignment regression source. Do not invent evidence if the control corpus is not in the repo.

```python
run = verify_assignment(requirements_56, control_page_corpus)
assert len(run.requirements) == 56
assert len(run.routes) == 56
assert len(run.decisions) == 56
assert all(route.verification_kind for route in run.routes.values())
assert all(decision.trace_id for decision in run.decisions.values())
```

- [ ] **Step 5: Verify GREEN**

Run: `pytest -q tests/core25`

Expected: all core25 tests pass.

- [ ] **Step 6: Commit**

```bash
git add core25/pipeline.py core25/__init__.py tests/core25/test_assignment_pipeline.py
git commit -m "feat(core25): add unified assignment pipeline"
```

---

### Task 8: Test 78 Golden Set, persistence, provider failure, and release gate

**Files:**
- Create: `core25/golden/__init__.py`
- Create: `core25/golden/test78.py`
- Create: `tests/core25/test_golden_test78.py`
- Modify `.github/workflows/...` only if the current workflow does not already discover `tests/core25`.

**Interfaces:**
- Produces deterministic Golden Set scenarios executed through production `core25` code.

- [ ] **Step 1: Write failing Golden Set test**

```python
from core25.golden.test78 import scenarios


def test_test78_defect_classes_are_frozen_as_regressions():
    names = {scenario.name for scenario in scenarios()}
    assert names >= {
        "toc_not_proof",
        "wrong_owner",
        "wrong_parameter",
        "owner_section_absent",
        "judge_without_canonical_proof",
        "provider_429_not_success",
        "nan_not_categorical",
        "canonical_trace_persists",
        "semantic_positive_without_selected_evidence",
    }
```

- [ ] **Step 2: Verify RED**

Run: `pytest -q tests/core25/test_golden_test78.py`

Expected: Golden Set module missing.

- [ ] **Step 3: Implement scenarios using real production pipeline**

Each scenario contains compact source dictionaries and an assertion callback. No scenario may patch a final verdict. `nan_not_categorical` must cover `float("nan")` and string `"nan"`. `provider_429_not_success` supplies normalized provider context `{"status": "ERROR", "http_status": 429}` and must terminate non-categorically. Persistence must JSON-round-trip IDs plus document/page/fragment without loss.

- [ ] **Step 4: Verify Golden Set GREEN**

Run: `pytest -q tests/core25/test_golden_test78.py`

Expected: pass.

- [ ] **Step 5: Run targeted regression gate**

Run:
```bash
pytest -q tests/core25 \
  test_core20_alpha1012_evidence_quality.py \
  test_core20_alpha1013_proof_trace.py \
  test_evidence_driven_requirements_100.py \
  test_evidence_provenance_96.py \
  test_binding_integrity_risk_hotfix_9512.py \
  test_processing_binding_reliability_92.py \
  test_project_understanding_95.py \
  test_trust_pipeline_100a5.py
```

Expected: zero failures.

- [ ] **Step 6: Run full available-fixture suite**

Run: `pytest -q`

Expected: zero product failures. Historical tests that explicitly depend on absent external `/mnt/data` fixtures must be reported as fixture-unavailable, not “fixed” by weakening product logic.

- [ ] **Step 7: Verify CI discovery**

Fetch the current workflow before editing it. If pytest already discovers `tests/core25`, make no workflow change. Otherwise add `tests/core25` to the existing test job. Require green existing `core20-tests` / `results-integrity` equivalents and the new core25 group before Alpha 1 completion.

- [ ] **Step 8: Commit**

```bash
git add core25/golden tests/core25 .github/workflows
git commit -m "test(core25): add Test 78 golden quality gate"
```

---

## Alpha 1 completion review

Do not declare Alpha 1 complete until fresh command output proves all ten gates:

1. 56/56 Assignment requirements represented as `Requirement25`.
2. 56/56 have explicit scope and verification route.
3. Zero categorical decisions without canonical evidence.
4. Zero categorical cross-owner comparisons.
5. TOC/index-only evidence never satisfies proof.
6. Every categorical result preserves document + page + fragment.
7. Initial Test 78 Golden Set is automated and green.
8. Existing targeted core20 regressions are green.
9. Provider/Judge/Critic-only cases remain non-categorical.
10. Persistence round-trip preserves the complete canonical trace.
