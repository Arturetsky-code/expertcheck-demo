from . import project, objects, checks, checklists, issues, reports, settings, advisor, risks, workspace, review_center, results_center, confirmation

PAGES={
    'Мои проекты': workspace.render,
    'Проект': project.render,
    'Подтверждение': confirmation.render,
    'Состав объектов': objects.render,
    'Межраздельная сверка': checks.render,
    'Риски экспертизы': risks.render,
    'Чек-листы': checklists.render,
    'Отчёт': reports.render,
    'Центр проверки': review_center.render,
    'Проверка': review_center.render,
    'Проверка': review_center.render,
    'Результаты': results_center.render,
    'Настройки': settings.render,
}
