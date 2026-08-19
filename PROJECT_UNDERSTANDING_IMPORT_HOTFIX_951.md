# ExpertCheck 9.5 Alpha 1.1 — Project Understanding Import Hotfix

Исправлен NameError на этапе 80% «Понимание проекта».

Причина: функции `build_project_object_model` и `understanding_quality` вызывались в `core/pipeline.py`, но их импорт отсутствовал в итоговой ZIP-сборке 9.5 Alpha 1.

Исправление:
- добавлен явный импорт из `core.project_understanding`;
- добавлен regression test на наличие символов в pipeline;
- проверен безопасный пустой Project Understanding model;
- полный pytest, compile и smoke test пройдены.
