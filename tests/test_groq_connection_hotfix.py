from core.ai_gateway import GroqProvider, diagnostic_message


def test_groq_auto_selects_available_model(monkeypatch):
    provider = GroqProvider('gsk_test', 'auto')

    def fake_get(url, headers, timeout=30):
        return 200, {'data': [{'id': 'openai/gpt-oss-20b'}]}

    def fake_post(url, headers, payload, timeout=45):
        assert payload['model'] == 'openai/gpt-oss-20b'
        return 200, {'choices': [{'message': {'content': 'OK'}}]}

    monkeypatch.setattr(provider, '_get', fake_get)
    monkeypatch.setattr(provider, '_post', fake_post)
    result = provider.test_connection()
    assert result.ok
    assert result.model == 'openai/gpt-oss-20b'


def test_groq_falls_back_after_model_permission_403(monkeypatch):
    provider = GroqProvider('gsk_test', 'auto')

    def fake_get(url, headers, timeout=30):
        return 200, {'data': [
            {'id': 'openai/gpt-oss-20b'},
            {'id': 'openai/gpt-oss-120b'},
        ]}

    calls = []
    def fake_post(url, headers, payload, timeout=45):
        calls.append(payload['model'])
        if payload['model'] == 'openai/gpt-oss-20b':
            return 403, {'error': {'message': 'model blocked at project level'}}
        return 200, {'choices': [{'message': {'content': 'OK'}}]}

    monkeypatch.setattr(provider, '_get', fake_get)
    monkeypatch.setattr(provider, '_post', fake_post)
    result = provider.test_connection()
    assert result.ok
    assert result.model == 'openai/gpt-oss-120b'
    assert calls == ['openai/gpt-oss-20b', 'openai/gpt-oss-120b']


def test_groq_403_diagnostic_mentions_permissions():
    from core.ai_gateway import AIResult
    message = diagnostic_message(AIResult(False, 'Groq', error='blocked', status_code=403))
    assert 'Model permissions' in message
