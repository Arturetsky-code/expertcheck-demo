# ExpertCheck 10.2 Alpha 2 — Deep Evidence Intelligence

Основная цель: повысить качество не количеством правил, а глубиной получения и проверки доказательств.

## Новое
- Project Evidence Database 2.0: единый read-optimised слой фактов, текстовых источников и подтверждённых конфликтов; владельцы фактов не додумываются.
- Evidence Retrieval Cascade: структурированные факты + точное совпадение сущности/показателя + семантические признаки + возможность AI judgement/reranking.
- Three-pass Review: реконструкция проекта → целевой поиск доказательств → adversarial review положительных выводов.
- Adversarial Gate: слабое текстовое evidence не может самостоятельно удержать итог «Соответствует».
- Подготовлена точка интеграции AI Evidence Judge: SUPPORTS / OTHER_ENTITY / OTHER_METRIC / CONTRADICTS / INSUFFICIENT.
- Добавлен базовый контур Historical Expert Benchmark (следующий шаг — импорт известных замечаний и измерение Expert Recall / Finding Precision).

## Принцип
Verification Factory формулирует, что проверять. Deep Evidence Intelligence отвечает, где доказательство и достаточно ли его для вывода.
