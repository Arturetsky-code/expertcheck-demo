from . import overview,documents,completeness,objects,checks,issues
PAGES={
    'Обзор':overview.render,
    'Документы':documents.render,
    'Комплектность':completeness.render,
    'Объекты':objects.render,
    'Сверки':checks.render,
    'Замечания':issues.render,
}
