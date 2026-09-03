from __future__ import annotations

"""Runtime preference for the last proven healthy free Gemini model.

The 18.2 agent preflight may already prove that one Flash model works while a
newer model is temporarily overloaded.  Qualification should not forget that
fact and spend the free quota retrying the overloaded model first on every
Streamlit rerun.
"""

from typing import Any

from core.free_ai_patch import AutoGeminiProvider

_LAST_GOOD_MODEL = ''
_INSTALLED = False


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    original = AutoGeminiProvider._generate_resilient

    def preferred_generate(
        self: AutoGeminiProvider,
        prompt: str,
        system: str = '',
        json_schema: dict[str, Any] | None = None,
        _known_models: list[str] | None = None,
    ):
        global _LAST_GOOD_MODEL
        benchmark_mode = 'provider_qualification' in str(prompt or '')
        previous_model = self.model

        # Prefer a model already proven healthy in this running Streamlit
        # process.  If there is no observation yet, 3.7 is preferred for the
        # qualification path because 3.8 may legitimately return HIGH_DEMAND;
        # AutoGeminiProvider still filters against the models actually exposed
        # to the user's key and falls back automatically.
        if benchmark_mode:
            self.model = _LAST_GOOD_MODEL or 'gemini-3.7-flash'

        try:
            result = original(
                self,
                prompt,
                system,
                json_schema=json_schema,
                _known_models=_known_models,
            )
        finally:
            self.model = previous_model

        if (
            getattr(result, 'ok', False)
            and getattr(result, 'model', '')
            and AutoGeminiProvider._is_free_text_candidate(str(result.model))
        ):
            _LAST_GOOD_MODEL = str(result.model)
        return result

    AutoGeminiProvider._generate_resilient = preferred_generate  # type: ignore[assignment]
    _INSTALLED = True
