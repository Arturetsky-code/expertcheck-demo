# ExpertCheck 5.1 Alpha 1 — Hybrid AI Engine

## Роли
- AI Extraction: классификация неоднозначных объектов, анализ ТЭП и пунктов чек-листа.
- AI Reviewer: быстрые объяснения и ответы инженеру по цифровой модели проекта.

## Провайдеры
- OpenRouter
- Groq
- DeepSeek
- Gemini (совместимость)

## Streamlit Secrets
```toml
OPENROUTER_API_KEY = "..."
OPENROUTER_MODEL = "openrouter/free"
GROQ_API_KEY = "..."
GROQ_MODEL = "auto"
DEEPSEEK_API_KEY = "..."
DEEPSEEK_MODEL = "deepseek-v4-flash"
```

DeepSeek требует положительного баланса; при HTTP 402 рекомендуется переключиться на Groq/OpenRouter.
