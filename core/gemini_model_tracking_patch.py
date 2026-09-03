from __future__ import annotations

"""Track the actual Gemini model used by the auto route for L5 qualification."""

from typing import Any

from core.free_ai_patch import AutoGeminiProvider

_INSTALLED = False


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    current = AutoGeminiProvider._generate_resilient
    if getattr(current, '_expertcheck_183_model_tracking', False):
        _INSTALLED = True
        return

    def tracked_generate(
        self: AutoGeminiProvider,
        prompt: str,
        system: str = '',
        json_schema: dict[str, Any] | None = None,
        _known_models: list[str] | None = None,
    ):
        result = current(
            self,
            prompt,
            system,
            json_schema=json_schema,
            _known_models=_known_models,
        )
        if getattr(result, 'ok', False) and getattr(result, 'model', ''):
            self.last_successful_model = str(result.model)
        return result

    tracked_generate._expertcheck_183_model_tracking = True  # type: ignore[attr-defined]
    AutoGeminiProvider._generate_resilient = tracked_generate  # type: ignore[assignment]
    _INSTALLED = True
