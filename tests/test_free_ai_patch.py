from __future__ import annotations

from core.free_ai_patch import AutoGeminiProvider


def test_gemini_discovery_filters_non_text_models(monkeypatch):
    provider = AutoGeminiProvider('test-key', 'auto')

    def fake_get(url, headers, timeout=12):
        return 200, {
            'models': [
                {'name': 'models/gemini-3.8-flash', 'supportedGenerationMethods': ['generateContent']},
                {'name': 'models/gemini-3.5-flash-lite', 'supportedGenerationMethods': ['generateContent']},
                {'name': 'models/gemini-embedding-001', 'supportedGenerationMethods': ['embedContent']},
                {'name': 'models/gemini-3.1-flash-image', 'supportedGenerationMethods': ['generateContent']},
            ]
        }

    monkeypatch.setattr(provider, '_get', fake_get)
    result, models = provider.available_models()
    assert result.ok is True
    assert models == ['gemini-3.8-flash', 'gemini-3.5-flash-lite']


def test_retired_configured_model_does_not_disable_gemini(monkeypatch):
    provider = AutoGeminiProvider('test-key', 'gemini-2.5-pro')
    provider._available_models_cache = ['gemini-3.8-flash', 'gemini-3.5-flash-lite']
    called = []

    def fake_post(url, headers, payload, timeout=45):
        called.append(url)
        return 200, {'candidates': [{'content': {'parts': [{'text': 'OK'}]}}]}

    monkeypatch.setattr(provider, '_post', fake_post)
    result = provider.test_connection()
    assert result.ok is True
    assert result.model == 'gemini-3.8-flash'
    assert called and 'gemini-3.8-flash:generateContent' in called[0]


def test_model_error_fails_over_to_next_available_flash(monkeypatch):
    provider = AutoGeminiProvider('test-key', 'auto')
    provider._available_models_cache = ['gemini-3.8-flash', 'gemini-3.7-flash']
    calls = []

    def fake_post(url, headers, payload, timeout=45):
        calls.append(url)
        if 'gemini-3.8-flash:' in url:
            return 404, {'error': {'message': 'model no longer available'}}
        return 200, {'candidates': [{'content': {'parts': [{'text': '{"verdict":"ok"}'}]}}]}

    monkeypatch.setattr(provider, '_post', fake_post)
    result = provider.generate_structured(
        'Проверьте пакет',
        'Верните JSON',
        json_schema={'type': 'object', 'properties': {'verdict': {'type': 'string'}}, 'required': ['verdict']},
    )
    assert result.ok is True
    assert result.model == 'gemini-3.7-flash'
    assert len(calls) == 2
    assert result.schema_mode == 'STRICT_JSON_SCHEMA'
