import json
from types import SimpleNamespace

from core.semantic_evidence_engine import build_evidence_packet, run_semantic_evidence_engine
from core.specialist_checker_factory import checker_profile


class FakeProvider:
    def __init__(self, name, role, *, hallucinate=False, accept=True, verdict="SUPPORTS"):
        self.name = name
        self.role = role
        self.hallucinate = hallucinate
        self.accept = accept
        self.verdict = verdict
        self.last_payload = None
        self.last_system = ""

    def generate(self, prompt, system=""):
        payload = json.loads(prompt)
        self.last_payload = payload
        self.last_system = system
        if self.role == "judge":
            decisions = []
            for packet in payload["packets"]:
                evidence_id = "SE-HALLUCINATED" if self.hallucinate else packet["evidence"][0]["evidence_id"]
                decisions.append({
                    "packet_id": packet["packet_id"], "verdict": self.verdict,
                    "evidence_ids": [evidence_id], "same_entity": True,
                    "same_property": True, "qualifiers_satisfied": True,
                    "modality_satisfied": True, "confidence": 0.94,
                    "reason": "Адресный фрагмент прямо подтверждает атомарное условие.",
                })
            body = {"decisions": decisions}
        else:
            reviews = []
            for packet in payload["packets"]:
                evidence_ids = list((packet.get("judge_decision") or {}).get("evidence_ids") or [])
                reviews.append({
                    "packet_id": packet["packet_id"], "accept": self.accept,
                    "evidence_ids": evidence_ids,
                    "blocking_concerns": [] if self.accept else ["Не доказан критический квалификатор."],
                    "confidence": 0.91, "reason": "Независимая проверка завершена.",
                })
            body = {"reviews": reviews}
        return SimpleNamespace(ok=True, text=json.dumps(body, ensure_ascii=False), provider=self.name, model=f"{self.name}-test")


def _row(*, contradiction=False):
    evidence = {
        "document": "Раздел ПД №2_ПЗУ1.pdf", "page": 27, "section": "ПЗУ",
        "text": "Проектом предусмотрено освещение территории светодиодными светильниками на металлических опорах.",
        "contract_state": "SATISFIED", "semantic_gate_state": "PASSED",
        "semantic_verdict": "CONTRADICTS" if contradiction else "SUPPORTS",
        "source_modality": "TEXT_OR_TABLE", "design_marker": True, "score": 94,
    }
    return {
        "atom_id": "REQ-1-A001", "parent_requirement_id": "REQ-1", "domain": "assignment",
        "atom_text": "Предусмотреть освещение территории светодиодными светильниками на металлических опорах.",
        "atomic_kind": "PRESENCE_REQUIREMENT", "status": "Требует проверки",
        "verification_kind": "REVIEW_QUESTION", "final_verification_kind": "REVIEW_QUESTION",
        "proof_kind": "CANDIDATE_EVIDENCE", "evidence_candidates": [evidence],
        "verification_recipe": {
            "recipe_id": "AR-REQ-1-A001", "check_method": "ATOMIC_PATTERN_PRESENCE",
            "expected_sections": ["ПЗУ"], "required_modality": "TEXT_OR_TABLE",
            "recipe_status": "RETRIEVAL_ONLY", "categorical_verdict_allowed": False,
        },
        "evidence_contract_v2": {
            "scope": "SITE_SPECIFIC", "expected_sections": ["ПЗУ"],
            "required_modality": "TEXT_OR_TABLE", "critical_qualifiers": ["светодиод", "металлическ"],
        },
    }


def test_packet_reaches_l4_only_with_addressable_contract_ready_evidence():
    packet = build_evidence_packet(_row(), {"facts": [], "passages": []})
    assert packet["evidence_level"] == "L4"
    assert packet["evidence"][0]["source_locator"] == "Раздел ПД №2_ПЗУ1.pdf, стр. 27"


def test_independent_judge_and_critic_promote_only_to_l5():
    row = _row()
    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=FakeProvider("OpenRouter", "judge"),
        critic_provider=FakeProvider("Groq", "critic"),
    )
    assert audit["promoted_verified"] == 1
    assert row["verification_kind"] == "VERIFIED_OK"
    assert row["evidence_level"] == "L5"
    assert row["specialized_checker_id"] == "SEMANTIC_EVIDENCE_CONSENSUS_V1"


def test_same_actual_provider_blocks_consensus_even_for_two_configured_roles():
    row = _row()
    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=FakeProvider("Groq", "judge"),
        critic_provider=FakeProvider("Groq", "critic"),
    )
    assert audit["promoted_verified"] == 0
    assert row["verification_kind"] == "REVIEW_QUESTION"
    assert row["evidence_level"] == "L4"
    assert any("одним AI-провайдером" in reason for reason in row["semantic_consensus_reasons"])


def test_hallucinated_evidence_id_is_rejected_before_critic():
    row = _row()
    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=FakeProvider("OpenRouter", "judge", hallucinate=True),
        critic_provider=FakeProvider("Groq", "critic"),
    )
    assert audit["promoted_verified"] == 0
    assert audit["critic_responses"] == 0
    assert row["evidence_level"] == "L4"


def test_critic_concern_blocks_promotion():
    row = _row()
    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=FakeProvider("OpenRouter", "judge"),
        critic_provider=FakeProvider("Groq", "critic", accept=False),
    )
    assert audit["promoted_verified"] == 0
    assert row["verification_kind"] == "REVIEW_QUESTION"


def test_ai_contradiction_requires_explicit_machine_readable_conflict():
    row = _row(contradiction=False)
    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=FakeProvider("OpenRouter", "judge", verdict="CONTRADICTS"),
        critic_provider=FakeProvider("Groq", "critic"),
    )
    assert audit["project_findings"] == 0
    assert row["verification_kind"] == "REVIEW_QUESTION"


def test_explicit_conflict_survives_independent_consensus():
    row = _row(contradiction=True)
    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=FakeProvider("OpenRouter", "judge", verdict="CONTRADICTS"),
        critic_provider=FakeProvider("Groq", "critic"),
    )
    assert audit["project_findings"] == 1
    assert row["verification_kind"] == "PROJECT_FINDING"
    assert row["evidence_level"] == "L5"


def test_normative_clause_remains_specialist_only_without_verified_kb_clause():
    profile = checker_profile({"atomic_kind": "NORMATIVE_CLAUSE"}, {"check_method": "CLAUSE_ADDRESSED_NORMATIVE_CHECK"})
    assert profile["checker_mode"] == "SPECIALIST"
    assert profile["consensus_eligible"] is False


def test_external_agent_payload_is_bounded_and_pseudonymised():
    row = _row()
    row["evidence_candidates"][0]["text"] += " Контакт: expert@example.ru. Шифр RAM-SECRET-777."
    judge = FakeProvider("OpenRouter", "judge")
    critic = FakeProvider("Groq", "critic")
    run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=judge, critic_provider=critic,
    )
    outbound = json.dumps(judge.last_payload, ensure_ascii=False)
    assert "Раздел ПД №2_ПЗУ1.pdf" not in outbound
    assert "DOC-001" in outbound
    assert "expert@example.ru" not in outbound and "[EMAIL]" in outbound
    assert "RAM-SECRET-777" not in outbound and "[ШИФР]" in outbound
    assert "недоверенными цитируемыми данными" in judge.last_system
    critic_outbound = json.dumps(critic.last_payload, ensure_ascii=False)
    assert "Раздел ПД №2_ПЗУ1.pdf" not in critic_outbound
