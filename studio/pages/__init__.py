from . import project, objects, checks, checklists, issues, reports, settings

PAGES={
    'Проект': project.render,
    'Объекты': objects.render,
    'Межраздельная сверка': checks.render,
    'Чек-листы': checklists.render,
    'Замечания': issues.render,
    'Отчёты': reports.render,
    'Настройки': settings.render,
}
