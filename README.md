# ExpertCheck Core 2.0 Alpha 3

Переходная рабочая сборка ядра ExpertCheck для Streamlit Community Cloud.

## Изменения Alpha 3

- исправлен порядок возвращаемых данных из Legacy Analyzer;
- Table Engine теперь реально анализирует страницы загруженных PDF и связывает тип таблицы с находками;
- добавлены поля `table_type`, `table_score`, `table_evidence`;
- Semantic Engine оценивает связь характеристики с реестровой записью объекта;
- добавлены `semantic_match_score`, `semantic_match_reasons`, `semantic_anchor_name`;
- результаты проверок связываются с правилами из `knowledge/core/rules.json`;
- для документов выводится количество страниц, распознанных как инженерные таблицы;
- усилена самопроверка структуры папки `knowledge`.

## Развёртывание

Загрузите **содержимое** этой папки в корень GitHub-репозитория. В корне должны быть:

```text
app.py
analyzer.py
legacy_analyzer.py
requirements.txt
core/
knowledge/
parameters.json
objects.json
document_types.json
engineering_rules.json
```

Основной файл Streamlit: `app.py`.

После коммита выполните `Manage app → Reboot app`.

## Локальная проверка структуры

```bash
python smoke_test.py
```

## Архитектурный статус

Legacy Analyzer пока остаётся источником проверенной предметной логики. Core 2.0 уже самостоятельно выполняет:

1. загрузку каталогов знаний;
2. классификацию инженерных таблиц;
3. расчёт объяснимой уверенности;
4. семантическое сопоставление объектов;
5. привязку результатов к каталогу правил.
