from __future__ import annotations

from core import provider_benchmark
from core.free_ai_patch import AutoGeminiProvider, install


def test_gemini_benchmark_uses_short_timeout_and_two_attempts(monkeypatch):
    provider = AutoGeminiProvider('test-key', 'auto')
    provider._available_models_cache = ['gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.6-flash']
    calls = []

    def fake_post(url, headers, payload, timeout=45):
        calls.append((url, timeout))
        if len(calls) == 1:
            return 503, {'error': {'message': 'high demand, try again later'}}
        return 200, {'candidates': [{'content': {'parts': [{'text': '{"decisions":[]}'}]}}]}

    monkeypatch.setattr(provider, '_post', fake_post)
    result = provider.generate(
        '{"task":"provider_qualification","packets":[]}',
        'Верните JSON',
    )

    assert result.ok is True
    assert len(calls) == 2
    assert all(timeout == provider.BENCHMARK_TIMEOUT_SECONDS for _, timeout in calls)
    assert result.model == 'gemini-3.7-flash'


def test_gemini_benchmark_advances_only_one_logical_call(monkeypatch):
    install()
    provider = AutoGeminiProvider('test-key', 'auto')

    executed = []

    def fake_execute(provider_arg, batch, *, repeat, batch_number):
        executed.append((repeat, batch_number))
        return ({
            'repeat': repeat,
            'batch': batch_number,
            'requested': len(batch),
            'ok': True,
            'schema_ok': True,
            'provider': 'Gemini',
            'model': 'gemini-3.7-flash',
            'status_code': 200,
            'latency_ms': 100,
            'schema_mode': 'STRICT_JSON_SCHEMA',
            'error': '',
        }, [])

    monkeypatch.setattr(provider_benchmark, '_execute_batch', fake_execute)
    state = provider_benchmark.start_provider_benchmark(provider, repeats=3, batch_size=5)
    updated = provider_benchmark.advance_provider_benchmark(provider, state, max_calls=3)

    assert len(executed) == 1
    assert updated['next_call_index'] == 1
    assert updated['completed'] is False
    assert updated['version'] == '18.2-provider-qualification-v3'
