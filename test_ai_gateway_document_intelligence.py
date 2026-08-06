from core.ai_gateway import GeminiProvider, OpenRouterProvider, diagnostic_message
from core.document_intelligence import classify_zone, redact_text, build_structured_ai_context


def test_service_zone_cannot_create_object():
    decision = classify_zone({'section_title': 'Состав проектной документации'})
    assert decision.zone == 'DOCUMENT_SERVICE'
    assert not decision.can_create_object


def test_object_register_is_trusted_zone():
    decision = classify_zone({'table_title': 'Состав сложного объекта'})
    assert decision.zone == 'OBJECT_REGISTER'
    assert decision.can_create_object


def test_redaction_hides_email_and_code():
    text = redact_text('test@example.com RAM-0207.2-ЗД-ПД-ПЗУ2')
    assert '[EMAIL]' in text
    assert '[ШИФР]' in text


def test_context_is_compact_and_structured():
    context = build_structured_ai_context([
        {'Позиция по ГП': '4.13', 'Наименование объекта': 'Здание', 'Включить': True}
    ], [{'object': 'Здание', 'status': 'Совпадает'}])
    assert context['objects'][0]['position'] == '4.13'
    assert context['cross_checks'][0]['status'] == 'Совпадает'


def test_empty_keys_return_clear_error():
    assert not GeminiProvider('', 'gemini-2.5-flash').generate('x').ok
    assert not OpenRouterProvider('', 'openrouter/free').generate('x').ok


def test_diagnostic_401():
    from core.ai_gateway import AIResult
    assert 'недействителен' in diagnostic_message(AIResult(False, 'x', error='bad', status_code=401)).lower()


def test_groq_empty_key_returns_clear_error():
    from core.ai_gateway import GroqProvider
    result = GroqProvider('', 'llama-3.3-70b-versatile').generate('x')
    assert not result.ok
    assert 'Groq' in result.error


def test_auto_provider_is_created_with_keys(monkeypatch):
    from core.ai_gateway import provider_from_settings, FailoverProvider
    monkeypatch.setenv('OPENROUTER_API_KEY', 'or-test')
    monkeypatch.setenv('GROQ_API_KEY', 'gsk-test')
    provider = provider_from_settings('Авто: Groq → OpenRouter')
    assert isinstance(provider, FailoverProvider)
    assert [p.name for p in provider.providers] == ['Groq', 'OpenRouter']
