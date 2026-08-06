from __future__ import annotations

import json
import os
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
    def _post(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int = 45) -> tuple[int, dict[str, Any]]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json', **headers},
            method='POST',
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

    def generate(self, prompt: str, system: str = '') -> AIResult:
        if not self.api_key:
            return AIResult(False, self.name, error='API-ключ Groq не задан.', model=self.model)
        model = self.model or 'llama-3.3-70b-versatile'
        messages=[]
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        payload = {
            'model': model, 'messages': messages, 'temperature': 0.1,
            'max_tokens': 1600, 'response_format': {'type': 'json_object'} if 'JSON' in system.upper() else None,
        }
        if payload['response_format'] is None:
            payload.pop('response_format')
        headers = {'Authorization': f'Bearer {self.api_key}'}
        status, body = self._post('https://api.groq.com/openai/v1/chat/completions', headers, payload)
        if status != 200:
            message = (((body.get('error') or {}).get('message')) or str(body))
            return AIResult(False, self.name, error=message, status_code=status, model=model)
        try:
            text = body['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError):
            return AIResult(False, self.name, error='Groq вернул ответ без текста.', status_code=status, model=model)
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
            if result.status_code not in {0, 408, 429, 500, 502, 503, 504}:
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
    if provider_key == 'gemini':
        return GeminiProvider(get('GEMINI_API_KEY'), get('GEMINI_MODEL', 'gemini-2.5-flash'))
    if provider_key == 'openrouter':
        return OpenRouterProvider(get('OPENROUTER_API_KEY'), get('OPENROUTER_MODEL', 'openrouter/free'))
    if provider_key == 'groq':
        return GroqProvider(get('GROQ_API_KEY'), get('GROQ_MODEL', 'llama-3.3-70b-versatile'))
    if provider_key in {'авто: openrouter → groq', 'auto-openrouter-groq'}:
        return FailoverProvider([
            OpenRouterProvider(get('OPENROUTER_API_KEY'), get('OPENROUTER_MODEL', 'openrouter/free')),
            GroqProvider(get('GROQ_API_KEY'), get('GROQ_MODEL', 'llama-3.3-70b-versatile')),
        ])
    if provider_key in {'авто: groq → openrouter', 'auto-groq-openrouter'}:
        return FailoverProvider([
            GroqProvider(get('GROQ_API_KEY'), get('GROQ_MODEL', 'llama-3.3-70b-versatile')),
            OpenRouterProvider(get('OPENROUTER_API_KEY'), get('OPENROUTER_MODEL', 'openrouter/free')),
        ])
    return None


def diagnostic_message(result: AIResult) -> str:
    if result.ok:
        return f'Подключение успешно. Провайдер: {result.provider}; модель: {result.model}.'
    code = result.status_code
    if code == 401:
        return 'Ключ недействителен или отозван.'
    if code == 402:
        return 'Недостаточно кредитов или бесплатный лимит исчерпан.'
    if code == 403:
        return 'Доступ запрещён настройками ключа или провайдера.'
    if code == 429:
        return 'Превышен лимит запросов. Повторите позже.'
    if code in {502, 503}:
        return 'Выбранная модель временно недоступна.'
    if code == 0:
        return 'Сетевая ошибка: ' + result.error
    return f'Ошибка API{f" HTTP {code}" if code else ""}: {result.error}'
