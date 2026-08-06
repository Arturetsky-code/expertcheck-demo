# Groq Connection Hotfix

- Проверка ключа выполняется через `GET /openai/v1/models`.
- `GROQ_MODEL = "auto"` автоматически выбирает доступную модель.
- При 403 приложение пробует альтернативные модели и показывает сведения о Model Permissions.
- При JSON-задачах предусмотрен повтор запроса без `response_format`, если конкретная модель его не принимает.
- `llama-3.3-70b-versatile` больше не является моделью по умолчанию.

Рекомендуемые Secrets:

```toml
GROQ_API_KEY = "gsk_..."
GROQ_MODEL = "auto"
```
