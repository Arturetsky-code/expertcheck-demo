from . import project, objects, checks, checklists, issues, reports, settings, advisor, risks, workspace

PAGES={
    'Мои проекты': workspace.render,
    'Проект': project.render,
    'Состав объектов': objects.render,
    'Межраздельная сверка': checks.render,
    'Риски экспертизы': risks.render,
    'Чек-листы': checklists.render,
    'Отчёт': reports.render,
    'Настройки': settings.render,
}
