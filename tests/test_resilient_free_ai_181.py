from __future__ import annotations

import json
from unittest.mock import patch

from core.ai_gateway import AIResult, FailoverProvider, GeminiProvider, diagnostic_message, provider_for_role, provider_from_settings
from core.provider_benchmark import BENCHMARK_VERSION, advance_provider_benchmark, benchmark_cases, start_provider_benchmark
from core.semantic_evidence_engine import run_semantic_evidence_engine, valid_structured_contract
from tests.test_semantic_evidence_engine_140a1 import FakeProvider, _row


def _decision(packet: dict) -> dict:
    expected = next(
        case["expected_verdict"]
        for case in benchmark_cases()
        if case["case_id"] == packet["packet_id"]
    )
    positive = expected in {"SUPPORTS", "CONTRADICTS"}
    return {
        "packet_id": packet["packet_id"],
        "verdict": expected,
        "evidence_ids": [packet["evidence"][0]["evidence_id"]] if positive else [],
        "same_entity": expected != "OTHER_ENTITY",
        "same_property": expected != "OTHER_METRIC",
        "qualifiers_satisfied": positive,
        "modality_satisfied": positive,
        "confidence": 0.99,
        "reason": "Синтетический ответ.",
    }


class PerfectGroq:
    name = "Groq"
    model = "openai/gpt-oss-120b"
    api_key = "configured"

    def generate_validated(self, prompt, system="", validator=None, json_schema=None):
        payload = json.loads(prompt)
        text = json.dumps({"decisions": [_decision(row) for row in payload["packets"]]}, ensure_ascii=False)
        return AIResult(
            True, self.name, text=text, status_code=200, model=self.model,
            latency_ms=25, schema_mode="STRICT_JSON_SCHEMA",
        )


class RateLimitedThenPerfect(PerfectGroq):
    def __init__(self):
        self.attempts = 0

    def generate_validated(self, prompt, system="", validator=None, json_schema=None):
        self.attempts += 1
        if self.attempts == 1:
            return AIResult(
                False, self.name, status_code=429, model=self.model,
                error="Rate limit reached. Please try again in 9.42s.",
            )
        return super().generate_validated(prompt, system, validator, json_schema)


def test_gemini_uses_native_json_schema_and_auth_header():
    provider = GeminiProvider("gemini-secret", "gemini-2.5-pro")
    captured = {}

    def fake_post(url, headers, payload, timeout=45):
        captured.update({"url": url, "headers": headers, "payload": payload})
        return 200, {"candidates": [{"content": {"parts": [{"text": '{"decisions":[]}' }]}}]}

    provider._post = fake_post
    schema = {
        "type": "object",
        "properties": {"decisions": {"type": "array", "items": {"type": "object"}}},
        "required": ["decisions"],
    }
    result = provider.generate_structured("{}", "Верните JSON", json_schema=schema)

    assert result.ok is True
    assert result.schema_mode == "STRICT_JSON_SCHEMA"
    assert "key=" not in captured["url"]
    assert captured["headers"]["x-goog-api-key"] == "gemini-secret"
    assert captured["payload"]["generationConfig"]["responseMimeType"] == "application/json"
    assert captured["payload"]["generationConfig"]["responseJsonSchema"] == schema


def test_free_groq_gemini_failover_route_is_available():
    with patch.dict(
        "os.environ",
        {"GROQ_API_KEY": "gsk-test", "GEMINI_API_KEY": "gemini-test"},
        clear=False,
    ):
        provider = provider_from_settings("Авто: Groq → Gemini")
    assert isinstance(provider, FailoverProvider)
    assert [row.name for row in provider.providers] == ["Groq", "Gemini"]


def test_rate_limit_is_checkpointed_without_poisoning_semantic_metrics():
    provider = RateLimitedThenPerfect()
    state = start_provider_benchmark(provider)

    state = advance_provider_benchmark(provider, state, max_calls=3, now=100)
    assert state["next_call_index"] == 0
    assert state["retry_after_seconds"] == 12
    assert len(state["transport_events"]) == 1
    assert state["summary"]["metrics"]["case_observations"] == 0

    unchanged = advance_provider_benchmark(provider, state, max_calls=3, now=105)
    assert unchanged["next_call_index"] == 0
    assert provider.attempts == 1

    resumed = advance_provider_benchmark(provider, unchanged, max_calls=1, now=113)
    assert resumed["next_call_index"] == 1
    assert resumed["summary"]["metrics"]["semantic_accuracy_pct"] == 100.0
    assert resumed["summary"]["metrics"]["rate_limit_events"] == 1


def test_groq_benchmark_slice_stops_before_free_tpm_burst():
    provider = PerfectGroq()
    state = advance_provider_benchmark(provider, start_provider_benchmark(provider), max_calls=3, now=100)
    assert state["next_call_index"] == 3
    assert state["completed"] is False
    assert state["cooldown_until"] == 160
    assert state["summary"]["metrics"]["benchmark_completion_pct"] == 16.7


def test_expired_benchmark_cooldown_is_cleared_before_resume():
    provider = PerfectGroq()
    cases = benchmark_cases()[:1]
    state = start_provider_benchmark(provider, repeats=1, batch_size=1, cases=cases)
    state["cooldown_until"] = 100
    state["retry_after_seconds"] = 60

    completed = advance_provider_benchmark(
        provider, state, max_calls=1, now=101, cases=cases,
    )

    assert completed["completed"] is True
    assert completed["cooldown_until"] == 0.0
    assert completed["retry_after_seconds"] == 0


def test_local_contract_rejects_incomplete_schema_even_after_http_success():
    incomplete = json.dumps({
        "decisions": [{"packet_id": "P-1", "verdict": "SUPPORTS"}],
    })
    assert valid_structured_contract(incomplete) is False


def test_rate_limit_diagnostic_reports_safe_retry():
    result = AIResult(
        False, "Groq", status_code=429,
        error="Rate limit reached. Please try again in 9.42s.",
    )
    message = diagnostic_message(result)
    assert "бесплатный лимит" in message.lower()
    assert "9 с" in message


def test_semantic_roles_require_current_completed_qualification_for_l5():
    state = {
        "ai_judge_provider": "Groq",
        "provider_benchmark_results": {},
    }
    with patch.dict("os.environ", {"GROQ_API_KEY": "gsk-test"}, clear=False):
        unqualified = provider_for_role("judge", state)
    assert unqualified.qualification_required is True
    assert unqualified.qualification_passed is False

    state["provider_benchmark_results"] = {
        "Groq": {
            "version": BENCHMARK_VERSION,
            "completed": True,
            "qualified": True,
        }
    }
    with patch.dict("os.environ", {"GROQ_API_KEY": "gsk-test"}, clear=False):
        qualified = provider_for_role("judge", state)
    assert qualified.qualification_passed is True


def test_unqualified_production_provider_cannot_promote_semantic_l5():
    row = _row()
    judge = FakeProvider("Groq", "judge")
    critic = FakeProvider("Gemini", "critic")
    judge.qualification_required = True
    critic.qualification_required = True
    judge.qualification_passed = True
    critic.qualification_passed = False

    audit = run_semantic_evidence_engine(
        [row], fact_graph={"facts": [], "passages": []}, level="extended", limit=10,
        judge_provider=judge, critic_provider=critic,
    )

    assert audit["promoted_verified"] == 0
    assert row["evidence_level"] == "L4"
    assert any("квалификационный стенд" in reason for reason in audit["advisory_reasons"])
