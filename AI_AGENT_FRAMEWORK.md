# AI Agent Framework 1.0
AI-слой работает поверх подтверждённой цифровой модели проекта и не изменяет результаты Core автоматически.

Агенты: Object Analyst, Project Analyst, CrossCheck Analyst.

Режимы: локальный grounded-анализ и OpenAI API. Для API задайте `OPENAI_API_KEY`; необязательно `OPENAI_MODEL`.

Исходные PDF не отправляются во внешний API; используется `store=false`; выводы содержат `evidence_id`.
