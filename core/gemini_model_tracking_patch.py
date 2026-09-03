from __future__ import annotations

"""Track the actual Gemini model and activate the 18.4 verification runtime."""

from typing import Any

from core.free_ai_patch import AutoGeminiProvider

_INSTALLED = False


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    current = AutoGeminiProvider._generate_resilient
    if not getattr(current, '_expertcheck_183_model_tracking', False):
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

    # 18.4 deliberately reuses the existing startup hook instead of adding yet
    # another top-level patch import to app.py.  This keeps the release isolated
    # and easy to revert while the branch is under test.
    from core.verification_runtime_patch import install as install_verification_runtime
    install_verification_runtime()
    _INSTALLED = True
