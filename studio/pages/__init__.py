from . import project, objects, checks, checklists, ai_analysis, issues, reports, settings

PAGES={
    'Проект': project.render,
    'Объекты': objects.render,
    'Межраздельная сверка': checks.render,
    'Чек-листы': checklists.render,
    'AI-анализ': ai_analysis.render,
    'Замечания': issues.render,
    'Отчёты': reports.render,
    'Настройки': settings.render,
}
