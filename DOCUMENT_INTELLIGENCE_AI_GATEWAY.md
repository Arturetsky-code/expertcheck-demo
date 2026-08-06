# ExpertCheck 4.5 Alpha 1

## Document Intelligence

Добавлена единая классификация зон документа: служебные зоны, официальные объектные реестры, объектные таблицы ТЭП, поле чертежа и обычный текст. Обычный текст самостоятельно не создаёт объект.

## External AI Gateway

Поддерживаются подключаемые провайдеры:

- Google Gemini;
- OpenRouter;
- локальный советник без API.

Внешнему AI передаются только обезличенные структурированные данные: кандидаты объектов, решения Object Intelligence, результаты межраздельной сверки и доказательства. Полные PDF не передаются.

### Streamlit Secrets

```toml
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-2.5-flash"

OPENROUTER_API_KEY = "..."
OPENROUTER_MODEL = "openrouter/free"
```
