from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AIResult:
    ok: bool
    provider: str
    text: str = ''
    error: str = ''
    status_code: int | None = None
    model: str = ''


class AIProvider:
    name = 'base'

    def __init__(self, api_key: str, model: str):
        self.api_key = (api_key or '').strip()
        self.model = (model or '').strip()

    def test_connection(self) -> AIResult:
        return self.generate('Ответьте одним словом: OK')

    def generate(self, prompt: str, system: str = '') -> AIResult:
        raise NotImplementedError

    @staticmethod
    def _request(url: str, headers: dict[str, str], payload: dict[str, Any] | None = None, timeout: int = 20, method: str = 'POST') -> tuple[int, dict[str, Any]]:
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode('utf-8')
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'ExpertCheck/5.0 (+https://streamlit.io)',
                **headers,
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return int(response.status), json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode('utf-8', errors='replace')
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = {'error': {'message': raw}}
            return int(exc.code), body
        except (urllib.error.URLError, TimeoutError) as exc:
            return 0, {'error': {'message': str(exc)}}

    @classmethod
    def _post(cls, url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int = 20) -> tuple[int, dict[str, Any]]:
        return cls._request(url, headers, payload, timeout, 'POST')

    @classmethod
    def _get(cls, url: str, headers: dict[str, str], timeout: int = 15) -> tuple[int, dict[str, Any]]:
        return cls._request(url, headers, None, timeout, 'GET')


class GeminiProvider(AIProvider):
    name = 'Gemini'

    def generate(self, prompt: str, system: str = '') -> AIResult:
        if not self.api_key:
            return AIResult(False, self.name, error='API-ключ Gemini не задан.', model=self.model)
        model = self.model or 'gemini-2.5-flash'
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}'
        payload: dict[str, Any] = {
            'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 1600},
        }
        if system:
            payload['systemInstruction'] = {'parts': [{'text': system}]}
        status, body = self._post(url, {}, payload)
        if status != 200:
            message = (((body.get('error') or {}).get('message')) or str(body))
            return AIResult(False, self.name, error=message, status_code=status, model=model)
        try:
            text = body['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError, TypeError):
            return AIResult(False, self.name, error='Gemini вернул ответ без текста.', status_code=status, model=model)
        return AIResult(True, self.name, text=text, status_code=status, model=model)


class GroqProvider(AIProvider):
    name = 'Groq'

    FALLBACK_MODELS = (
        'openai/gpt-oss-20b',
        'openai/gpt-oss-120b',
        'qwen/qwen3.6-27b',
        'llama-3.3-70b-versatile',
    )

    @staticmethod
    def _clean_key(value: str) -> str:
        key = str(value or '').strip().strip('"').strip("'")
        if key.lower().startswith('bearer '):
            key = key[7:].strip()
        return key

    def __init__(self, api_key: str, model: str):
        super().__init__(self._clean_key(api_key), model)

    @property
    def headers(self) -> dict[str, str]:
        return {'Authorization': f'Bearer {self.api_key}'}

    def available_models(self) -> tuple[AIResult, list[str]]:
        if not self.api_key:
            return AIResult(False, self.name, error='API-ключ Groq не задан.'), []
        status, body = self._get('https://api.groq.com/openai/v1/models', self.headers)
        if status != 200:
            message = (((body.get('error') or {}).get('message')) or str(body))
            return AIResult(False, self.name, error=message, status_code=status), []
        models = [str(item.get('id', '')).strip() for item in (body.get('data') or []) if item.get('id')]
        return AIResult(True, self.name, text='Список моделей получен.', status_code=status), models

    def _candidate_models(self, available: list[str]) -> list[str]:
        configured = (self.model or '').strip()
        result: list[str] = []
        if configured and configured.lower() not in {'auto', 'авто', 'automatic'}:
            result.append(configured)
        for model in self.FALLBACK_MODELS:
            if model not in result:
                result.append(model)
        if available:
            result = [model for model in result if model in available]
            if not result:
                result = available[:3]
        return result

    def test_connection(self) -> AIResult:
        model_result, available = self.available_models()
        if not model_result.ok:
            return model_result
        if not self._candidate_models(available):
            return AIResult(False, self.name, error='Ключ действителен, но для проекта Groq не найдено доступных текстовых моделей.', status_code=403)
        return self.generate('Ответьте одним словом: OK', _known_models=available)

    def generate(self, prompt: str, system: str = '', _known_models: list[str] | None = None) -> AIResult:
        if not self.api_key:
            return AIResult(False, self.name, error='API-ключ Groq не задан.', model=self.model)

        available = list(_known_models or [])
        if not available:
            model_result, available = self.available_models()
            if not model_result.ok:
                return model_result

        messages=[]
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})

        attempts: list[str] = []
        last_result: AIResult | None = None
        for model in self._candidate_models(available):
            payload = {
                'model': model,
                'messages': messages,
                'temperature': 0.1,
                'max_tokens': 1600,
            }
            wants_json = 'JSON' in system.upper()
            if wants_json:
                payload['response_format'] = {'type': 'json_object'}

            status, body = self._post('https://api.groq.com/openai/v1/chat/completions', self.headers, payload)
            if status == 400 and wants_json:
                payload.pop('response_format', None)
                status, body = self._post('https://api.groq.com/openai/v1/chat/completions', self.headers, payload)

            if status == 200:
                try:
                    text = body['choices'][0]['message']['content']
                except (KeyError, IndexError, TypeError):
                    return AIResult(False, self.name, error='Groq вернул ответ без текста.', status_code=status, model=model)
                return AIResult(True, self.name, text=text, status_code=status, model=model)

            message = (((body.get('error') or {}).get('message')) or str(body))
            attempts.append(f'{model}: HTTP {status} — {message}')
            last_result = AIResult(False, self.name, error=message, status_code=status, model=model)

            if status in {401, 429, 500, 502, 503, 504}:
                break
            if status not in {400, 403, 404}:
                break

        if last_result is None:
            return AIResult(False, self.name, error='Groq не предоставил доступную модель.', status_code=403)
        return AIResult(
            False,
            self.name,
            error='Не удалось выполнить запрос ни к одной доступной модели. ' + ' | '.join(attempts),
            status_code=last_result.status_code,
            model=last_result.model,
        )


class DeepSeekProvider(AIProvider):
    name = 'DeepSeek'

    def generate(self, prompt: str, system: str = '') -> AIResult:
        if not self.api_key:
            return AIResult(False, self.name, error='API-ключ DeepSeek не задан.', model=self.model)
        model = self.model or 'deepseek-v4-flash'
        messages: list[dict[str, str]] = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        payload: dict[str, Any] = {
            'model': model,
            'messages': messages,
            'temperature': 0.1,
            'max_tokens': 2000,
        }
        if 'JSON' in system.upper():
            payload['response_format'] = {'type': 'json_object'}
        headers = {'Authorization': f'Bearer {self.api_key}'}
        status, body = self._post('https://api.deepseek.com/chat/completions', headers, payload, timeout=25)
        if status == 400 and 'response_format' in payload:
            payload.pop('response_format', None)
            status, body = self._post('https://api.deepseek.com/chat/completions', headers, payload, timeout=25)
        if status != 200:
            message = (((body.get('error') or {}).get('message')) or str(body))
            return AIResult(False, self.name, error=message, status_code=status, model=model)
        try:
            text = body['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError):
            return AIResult(False, self.name, error='DeepSeek вернул ответ без текста.', status_code=status, model=model)
        return AIResult(True, self.name, text=text, status_code=status, model=model)


class OpenRouterProvider(AIProvider):
    name = 'OpenRouter'

    def generate(self, prompt: str, system: str = '') -> AIResult:
        if not self.api_key:
            return AIResult(False, self.name, error='API-ключ OpenRouter не задан.', model=self.model)
        model = self.model or 'openrouter/free'
        messages=[]
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        payload = {'model': model, 'messages': messages, 'temperature': 0.1, 'max_tokens': 1600}
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'HTTP-Referer': os.getenv('EXPERTCHECK_PUBLIC_URL', 'https://expertcheck.local'),
            'X-Title': 'ExpertCheck',
        }
        status, body = self._post('https://openrouter.ai/api/v1/chat/completions', headers, payload)
        if status != 200:
            message = (((body.get('error') or {}).get('message')) or str(body))
            return AIResult(False, self.name, error=message, status_code=status, model=model)
        try:
            text = body['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError):
            return AIResult(False, self.name, error='OpenRouter вернул ответ без текста.', status_code=status, model=model)
        return AIResult(True, self.name, text=text, status_code=status, model=model)



def _is_cloudflare_1010(result: AIResult) -> bool:
    detail = str(result.error or '').lower()
    return (
        'error code: 1010' in detail
        or 'error 1010' in detail
        or ('cloudflare' in detail and '1010' in detail)
        or "banned your access based on your browser's signature" in detail
    )


def _is_retryable_provider_failure(result: AIResult) -> bool:
    if _is_cloudflare_1010(result):
        return True
    return result.status_code in {0, 408, 429, 500, 502, 503, 504}


class FailoverProvider(AIProvider):
    name = 'Автоматический резерв'

    def __init__(self, providers: list[AIProvider]):
        super().__init__('', '')
        self.providers = [p for p in providers if p and p.api_key]

    def test_connection(self) -> AIResult:
        return self.generate('Ответьте одним словом: OK')

    def generate(self, prompt: str, system: str = '') -> AIResult:
        if not self.providers:
            return AIResult(False, self.name, error='Не задан ни один API-ключ для резервного режима.')
        errors=[]
        for provider in self.providers:
            result=provider.generate(prompt, system)
            if result.ok:
                return result
            errors.append(f'{provider.name}: {diagnostic_message(result)}')
            if not _is_retryable_provider_failure(result):
                break
        return AIResult(False, self.name, error='; '.join(errors))


def provider_from_settings(provider: str, secrets: Any = None) -> AIProvider | None:
    provider_key = (provider or '').strip().lower()

    def get(name: str, default: str = '') -> str:
        value = ''
        if secrets is not None:
            try:
                value = secrets.get(name, '')
            except Exception:
                value = ''
        return str(value or os.getenv(name, default) or '')

    providers = {
        'openrouter': OpenRouterProvider(get('OPENROUTER_API_KEY'), get('OPENROUTER_MODEL', 'openrouter/free')),
        'groq': GroqProvider(get('GROQ_API_KEY'), get('GROQ_MODEL', 'auto')),
        'deepseek': DeepSeekProvider(get('DEEPSEEK_API_KEY'), get('DEEPSEEK_MODEL', 'deepseek-v4-flash')),
        'gemini': GeminiProvider(get('GEMINI_API_KEY'), get('GEMINI_MODEL', 'gemini-2.5-flash')),
    }
    aliases = {
        'авто: openrouter → groq': ['openrouter', 'groq'],
        'auto-openrouter-groq': ['openrouter', 'groq'],
        'авто: groq → openrouter': ['groq', 'openrouter'],
        'auto-groq-openrouter': ['groq', 'openrouter'],
        'авто: deepseek → openrouter → groq': ['deepseek', 'openrouter', 'groq'],
        'auto-deepseek-openrouter-groq': ['deepseek', 'openrouter', 'groq'],
        'авто: openrouter → groq → deepseek': ['openrouter', 'groq', 'deepseek'],
        'auto-openrouter-groq-deepseek': ['openrouter', 'groq', 'deepseek'],
        'гибридный ai': ['openrouter', 'groq', 'deepseek'],
        'hybrid': ['openrouter', 'groq', 'deepseek'],
    }
    if provider_key in providers:
        return providers[provider_key]
    if provider_key in aliases:
        return FailoverProvider([providers[name] for name in aliases[provider_key]])
    return None


def provider_for_role(role: str, session_state: Any, secrets: Any = None) -> AIProvider | None:
    role_key = (role or '').strip().lower()
    if role_key in {'extraction', 'извлечение', 'analysis'}:
        selected = session_state.get('ai_extraction_provider') or session_state.get('external_ai_provider', 'Отключён')
    else:
        selected = session_state.get('ai_reviewer_provider') or session_state.get('external_ai_provider', 'Отключён')
    return provider_from_settings(str(selected), secrets)


def diagnostic_message(result: AIResult) -> str:
    if result.ok:
        return f'Подключение успешно. Провайдер: {result.provider}; модель: {result.model}.'
    code = result.status_code
    if code == 401:
        return 'Ключ недействителен или отозван.'
    if code == 402:
        if result.provider == 'DeepSeek':
            return 'Недостаточно средств на балансе DeepSeek API. Пополните баланс или выберите Groq/OpenRouter.'
        return 'Недостаточно кредитов или бесплатный лимит исчерпан.'
    if code == 403:
        detail = str(result.error or '')
        if _is_cloudflare_1010(result):
            return (
                'Groq отклонил соединение на уровне Cloudflare (ошибка 1010). '
                'Это не ошибка API-ключа и не запрет модели: заблокирован сетевой запрос из текущего облачного окружения. '
                'Используйте режим «Авто: Groq → OpenRouter» или OpenRouter; приложение переключится на резерв автоматически. '
                'Подробности: ' + detail
            )
        if result.provider == 'Groq':
            return (
                'Ключ Groq распознан, но доступ к выбранной модели запрещён настройками организации или проекта. '
                'Проверьте Groq Console → Settings → Organization/Projects → Limits → Model permissions. '
                'Приложение уже попыталось подобрать другую доступную модель. Подробности: ' + detail
            )
        return 'Доступ запрещён настройками ключа или провайдера. ' + detail
    if code == 429:
        return 'Превышен лимит запросов. Повторите позже.'
    if code in {502, 503}:
        return 'Выбранная модель временно недоступна.'
    if code == 0:
        return 'Сетевая ошибка: ' + result.error
    return f'Ошибка API{f" HTTP {code}" if code else ""}: {result.error}'


def _extract_json(text: str) -> dict[str, Any] | list[Any] | None:
    raw = str(text or '').strip()
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.I | re.S)
    try:
        return json.loads(raw)
    except Exception:
        start_candidates=[i for i in (raw.find('{'),raw.find('[')) if i>=0]
        if not start_candidates:
            return None
        start=min(start_candidates)
        end=max(raw.rfind('}'),raw.rfind(']'))
        if end<=start:
            return None
        try:
            return json.loads(raw[start:end+1])
        except Exception:
            return None


def analyze_object_fragment(provider: AIProvider, fragment: dict[str, Any]) -> tuple[AIResult, dict[str, Any] | None]:
    system = '''Вы — модуль классификации инженерных сущностей. Верните только JSON без Markdown.\nСхема: {"entity_type":"project_object|equipment|document_service|context_object|unknown","design_status":"projected|reconstructed|existing|prospective|unknown","independent_object":true|false,"confidence":0.0,"reason":"...","recommended_action":"include|review|exclude"}. Не выдумывайте сведения и опирайтесь только на переданный фрагмент.'''
    prompt = 'Классифицируйте фрагмент проектной документации:\n' + json.dumps(fragment, ensure_ascii=False, indent=2)
    result = provider.generate(prompt, system)
    return result, _extract_json(result.text) if result.ok else None


def analyze_checklist_evidence(provider: AIProvider, item: dict[str, Any], evidence: list[dict[str, Any]]) -> tuple[AIResult, dict[str, Any] | None]:
    system = '''Вы — инженерный модуль проверки пункта чек-листа. Верните только JSON без Markdown.\nСхема: {"result":"yes|no|partial|requires_review|insufficient_data","confidence":0.0,"covered":[],"missing":[],"evidence_refs":[],"reason":"..."}. Не подменяйте инженерное решение предположением.'''
    payload={'checklist_item':item,'evidence':evidence[:20]}
    result=provider.generate(json.dumps(payload,ensure_ascii=False,indent=2),system)
    return result, _extract_json(result.text) if result.ok else None


def analyze_checklist_batch(provider: AIProvider, items: list[dict[str, Any]]) -> tuple[AIResult, dict[str, dict[str, Any]]]:
    """Semantic review of several checklist items in one request."""
    system = '''Вы — инженерный модуль смысловой проверки чек-листа проектной документации. Верните только JSON без Markdown.\nСхема: {"items":[{"key":"...","result":"yes|no|partial|requires_review|insufficient_data","confidence":0.0,"covered":[],"missing":[],"evidence_refs":[],"reason":"..."}]}. Используйте только переданные доказательства. Если доказательств мало, выберите insufficient_data или requires_review.'''
    payload = {'task': 'checklist_batch_review', 'items': items[:12]}
    result = provider.generate(json.dumps(payload, ensure_ascii=False, indent=2), system)
    parsed = _extract_json(result.text) if result.ok else None
    reviews: dict[str, dict[str, Any]] = {}
    if isinstance(parsed, dict):
        for row in parsed.get('items') or []:
            if isinstance(row, dict) and row.get('key'):
                reviews[str(row['key'])] = row
    return result, reviews
