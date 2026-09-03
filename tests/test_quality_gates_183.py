from __future__ import annotations

import json

from core import ai_gateway, semantic_evidence_engine as see
from core.quality_gates_patch import QualityGroqProvider, install


def _raw_support() -> dict:
    return {
        'packet_id': 'P-1',
        'verdict': 'SUPPORTS',
        'evidence_ids': ['E-1'],
        'same_entity': True,
        'same_property': True,
        'qualifiers_satisfied': True,
        'modality_satisfied': True,
        'confidence': 0.95,
        'reason': 'Совпадает число и единица.',
    }


def test_metric_gate_overrides_false_support_before_consensus():
    install()
    packet = {
        'packet_id': 'P-1',
        'evidence': [{
            'evidence_id': 'E-1',
            'owner_match': True,
            'property_match': False,
        }],
    }
    result = see._validate_judge(packet, _raw_support())
    assert result['verdict'] == 'OTHER_METRIC'
    assert result['same_property'] is False
    assert result['quality_gate_applied'] is True
    assert result['valid'] is True


def test_object_gate_overrides_false_support_before_consensus():
    install()
    packet = {
        'packet_id': 'P-1',
        'evidence': [{
            'evidence_id': 'E-1',
            'owner_match': False,
            'property_match': True,
        }],
    }
    result = see._validate_judge(packet, _raw_support())
    assert result['verdict'] == 'OTHER_ENTITY'
    assert result['same_entity'] is False
    assert result['quality_gate_applied'] is True
    assert result['valid'] is True


def test_groq_route_does_not_fall_through_to_blocked_project_models():
    provider = QualityGroqProvider('key', 'openai/gpt-oss-120b')
    assert provider._candidate_models([
        'openai/gpt-oss-120b',
        'openai/gpt-oss-20b',
        'qwen/qwen3.8-27b',
    ]) == ['openai/gpt-oss-120b']


def test_groq_failed_strict_json_retries_same_120b_in_json_object_mode(monkeypatch):
    provider = QualityGroqProvider('key', 'openai/gpt-oss-120b')
    provider._available_models_cache = ['openai/gpt-oss-120b']
    calls: list[dict] = []

    def fake_post(url, headers, payload, timeout=45):
        calls.append(dict(payload))
        if len(calls) == 1:
            return 400, {'error': {'message': 'Failed to generate JSON. Please adjust your prompt.'}}
        return 200, {'choices': [{'message': {'content': json.dumps({'decisions': []})}}]}

    monkeypatch.setattr(provider, '_post', fake_post)
    result = provider.generate_structured(
        '{}',
        'Верните только JSON',
        json_schema={'type': 'object', 'properties': {'decisions': {'type': 'array'}}, 'required': ['decisions']},
    )
    assert result.ok
    assert result.model == 'openai/gpt-oss-120b'
    assert len(calls) == 2
    assert calls[0]['response_format']['type'] == 'json_schema'
    assert calls[1]['response_format']['type'] == 'json_object'
