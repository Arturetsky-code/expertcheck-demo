from . import project, objects, checks, issues, reports
PAGES={
    'Проект': project.render,
    'Объекты': objects.render,
    'Проверки': checks.render,
    'Замечания': issues.render,
    'Отчёты': reports.render,
}
