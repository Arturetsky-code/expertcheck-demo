from __future__ import annotations

"""Runtime patch for the 18.2 free-first AI contour.

This module keeps the 18.1 semantic pipeline intact while replacing only the
Gemini transport lane with a resilient provider that discovers models actually
available to the configured API key. It deliberately prefers Flash/Flash-Lite
models because ExpertCheck 18.2 is designed to run without a required paid API.
"""

import time
from typing import Any

from core import ai_gateway


class AutoGeminiProvider(ai_gateway.GeminiProvider):
    """Gemini adapter with free-first model discovery and bounded failover."""

    FREE_FIRST_MODELS = (
        'gemini-3.8-flash',
        'gemini-3.7-flash',
        'gemini-3.6-flash',
        'gemini-3.5-flash-lite',
        'gemini-3.5-flash',
        'gemini-3.1-flash-lite',
        'gemini-2.5-flash-lite',
        'gemini-2.5-flash',
    )
    TRANSIENT_STATUS_CODES = frozenset({0, 408, 429, 500, 502, 503, 504})
    MAX_MODEL_ATTEMPTS = 4
    BENCHMARK_MODEL_ATTEMPTS = 2
    BENCHMARK_TIMEOUT_SECONDS = 18

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self._available_models_cache: list[str] | None = None

    @staticmethod
    def _normalise_model(value: str) -> str:
        model = str(value or '').strip()
        if model.startswith('models/'):
            model = model.split('/', 1)[1]
        return model

    @staticmethod
    def _is_free_text_candidate(model: str) -> bool:
        """Keep the automatic lane on text-capable Flash/Flash-Lite models.

        A stale explicit Pro model in Secrets must not be retried merely because
        the Gemini list-models endpoint still advertises it to the project.
        """
        low = str(model or '').lower()
        if 'gemini' not in low or 'flash' not in low:
            return False
        if any(token in low for token in ('embedding', 'image', 'tts', 'audio', 'live', 'pro')):
            return False
        return True

    def available_models(self) -> tuple[ai_gateway.AIResult, list[str]]:
        if self._available_models_cache is not None:
            return ai_gateway.AIResult(
                True, self.name,
                text='Список моделей Gemini получен из кэша.', status_code=200,
            ), list(self._available_models_cache)
        if not self.api_key:
            return ai_gateway.AIResult(False, self.name, error='API-ключ Gemini не задан.'), []
        status, body = self._get(
            'https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000',
            {'x-goog-api-key': self.api_key},
            timeout=12,
        )
        if status != 200:
            message = (((body.get('error') or {}).get('message')) or str(body))
            return ai_gateway.AIResult(False, self.name, error=message, status_code=status), []
        models: list[str] = []
        for item in body.get('models') or []:
            methods = set(item.get('supportedGenerationMethods') or [])
            name = self._normalise_model(item.get('name', ''))
            if not name or 'generateContent' not in methods:
                continue
            if self._is_free_text_candidate(name):
                models.append(name)
        self._available_models_cache = list(dict.fromkeys(models))
        return ai_gateway.AIResult(
            True, self.name,
            text='Список доступных бесплатных Gemini Flash-моделей получен.', status_code=200,
        ), list(self._available_models_cache)

    def _candidate_models(self, available: list[str]) -> list[str]:
        available_set = set(available)
        configured = self._normalise_model(self.model)
        candidates: list[str] = []

        # Honour an explicit model only when it still belongs to the free-first
        # Flash lane. Legacy/pro models from old Secrets are deliberately ignored.
        if (
            configured
            and configured.lower() not in {'auto', 'авто', 'automatic'}
            and self._is_free_text_candidate(configured)
        ):
            candidates.append(configured)

        for model in self.FREE_FIRST_MODELS:
            if model not in candidates:
                candidates.append(model)

        # Future Flash models returned by Gemini are accepted automatically.
        for model in sorted(
            (m for m in available if self._is_free_text_candidate(m)),
            key=lambda m: (0 if 'flash-lite' in m else 1, m),
        ):
            if model not in candidates:
                candidates.append(model)

        if available:
            candidates = [model for model in candidates if model in available_set]
        return candidates

    def test_connection(self) -> ai_gateway.AIResult:
        discovered, available = self.available_models()
        if not discovered.ok:
            return discovered
        if not self._candidate_models(available):
            return ai_gateway.AIResult(
                False, self.name,
                error='Ключ Gemini действителен, но не найдено доступных бесплатных Flash-моделей generateContent.',
                status_code=403,
            )
        return self._generate_resilient('Ответьте одним словом: OK', _known_models=available)

    def generate(self, prompt: str, system: str = '') -> ai_gateway.AIResult:
        return self._generate_resilient(prompt, system)

    def generate_structured(
        self,
        prompt: str,
        system: str = '',
        json_schema: dict[str, Any] | None = None,
    ) -> ai_gateway.AIResult:
        return self._generate_resilient(prompt, system, json_schema=json_schema)

    def _generate_resilient(
        self,
        prompt: str,
        system: str = '',
        json_schema: dict[str, Any] | None = None,
        _known_models: list[str] | None = None,
    ) -> ai_gateway.AIResult:
        if not self.api_key:
            return ai_gateway.AIResult(False, self.name, error='API-ключ Gemini не задан.', model=self.model)
        available = list(_known_models or [])
        if not available:
            discovered, available = self.available_models()
            if not discovered.ok:
                return discovered

        benchmark_mode = 'provider_qualification' in str(prompt or '')
        max_attempts = self.BENCHMARK_MODEL_ATTEMPTS if benchmark_mode else self.MAX_MODEL_ATTEMPTS
        request_timeout = self.BENCHMARK_TIMEOUT_SECONDS if benchmark_mode else 45

        attempts: list[str] = []
        last: ai_gateway.AIResult | None = None
        candidates = self._candidate_models(available)[:max_attempts]
        for model in candidates:
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
            generation_config: dict[str, Any] = {'temperature': 0.1, 'maxOutputTokens': 1600}
            if json_schema:
                generation_config.update({
                    'responseMimeType': 'application/json',
                    'responseJsonSchema': json_schema,
                })
            elif 'JSON' in system.upper():
                generation_config['responseMimeType'] = 'application/json'
            payload: dict[str, Any] = {
                'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
                'generationConfig': generation_config,
            }
            if system:
                payload['systemInstruction'] = {'parts': [{'text': system}]}
            started = time.perf_counter()
            status, body = self._post(
                url,
                {'x-goog-api-key': self.api_key},
                payload,
                timeout=request_timeout,
            )
            latency_ms = round((time.perf_counter() - started) * 1000)
            schema_mode = (
                'STRICT_JSON_SCHEMA' if json_schema
                else 'JSON_OBJECT' if 'JSON' in system.upper()
                else 'TEXT'
            )
            if status == 200:
                try:
                    text = body['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError, TypeError):
                    return ai_gateway.AIResult(
                        False, self.name,
                        error='Gemini вернул ответ без текста.',
                        status_code=status, model=model,
                        latency_ms=latency_ms, schema_mode=schema_mode,
                    )
                return ai_gateway.AIResult(
                    True, self.name, text=text, status_code=status, model=model,
                    latency_ms=latency_ms, schema_mode=schema_mode,
                )

            message = (((body.get('error') or {}).get('message')) or str(body))
            attempts.append(f'{model}: HTTP {status} — {message}')
            last = ai_gateway.AIResult(
                False, self.name, error=message, status_code=status, model=model,
                latency_ms=latency_ms, schema_mode=schema_mode,
            )
            lower = message.lower()
            model_problem = (
                status in {400, 403, 404}
                or 'no longer available' in lower
                or 'not found' in lower
                or 'not supported' in lower
            )
            transient_problem = (
                status in self.TRANSIENT_STATUS_CODES
                or 'high demand' in lower
                or 'temporarily unavailable' in lower
                or 'try again later' in lower
            )
            if model_problem or transient_problem:
                # Do not let one overloaded/retired model disable the Critic.
                # The attempt count is bounded to protect the free quota.
                continue
            break

        if last is None:
            return ai_gateway.AIResult(
                False, self.name,
                error='Gemini не предоставил рабочую бесплатную Flash-модель.',
                status_code=403,
            )
        return ai_gateway.AIResult(
            False,
            self.name,
            error='Не удалось выполнить запрос к доступным бесплатным Gemini Flash-моделям. ' + ' | '.join(attempts),
            status_code=last.status_code,
            model=last.model,
            latency_ms=last.latency_ms,
            schema_mode=last.schema_mode,
        )


def _install_benchmark_guard() -> None:
    """Make Gemini qualification responsive and safely resumable.

    Streamlit cannot repaint progress while one synchronous button handler is
    still running. Gemini therefore advances only one five-packet benchmark
    call per click/rerun. The provider itself also uses short benchmark-only
    timeouts and at most two model attempts, so the UI never silently waits
    through four 45-second fallbacks.
    """
    from core import provider_benchmark

    provider_benchmark.BENCHMARK_VERSION = '18.2-provider-qualification-v3'
    current = provider_benchmark.advance_provider_benchmark
    if getattr(current, '_expertcheck_gemini_guard', False):
        return

    original = current

    def guarded_advance(
        provider: Any,
        state: dict[str, Any] | None = None,
        *,
        max_calls: int = 3,
        now: float | None = None,
        cases: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if isinstance(provider, AutoGeminiProvider):
            max_calls = 1
        return original(
            provider,
            state,
            max_calls=max_calls,
            now=now,
            cases=cases,
        )

    guarded_advance._expertcheck_gemini_guard = True  # type: ignore[attr-defined]
    provider_benchmark.advance_provider_benchmark = guarded_advance


def install() -> None:
    """Install the provider patch once for all runtime role resolution."""
    if ai_gateway.GeminiProvider is not AutoGeminiProvider:
        ai_gateway.GeminiProvider = AutoGeminiProvider
    _install_benchmark_guard()
