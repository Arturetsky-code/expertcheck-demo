from __future__ import annotations

from typing import Any
import streamlit as st

_RESULT_LABELS = {
    'yes': 'Соответствует', 'no': 'Не соответствует', 'partial': 'Частично соответствует',
    'requires_review': 'Требует проверки', 'insufficient_data': 'Недостаточно данных',
    'project_object': 'Объект проекта', 'equipment': 'Оборудование', 'service_record': 'Служебная запись',
    'existing_object': 'Существующий объект', 'prospective_object': 'Перспективный объект',
    'include': 'Рекомендуется включить', 'exclude': 'Рекомендуется исключить', 'review': 'Проверить вручную',
    'projected': 'Проектируемый', 'reconstructed': 'Реконструируемый', 'existing': 'Существующий',
    'prospective': 'Перспективный', 'unknown': 'Не определено',
    'valid': 'Привязка подтверждена', 'suspicious': 'Привязка сомнительна', 'insufficient': 'Недостаточно данных',
    'keep': 'Оставить результат', 'requires_review': 'Требует проверки', 'suppress': 'Не использовать без проверки',
    'document_service': 'Служебный элемент документа', 'context_object': 'Контекстное упоминание',
}

_FIELD_LABELS = {
    'entity_type': 'Классификация', 'design_status': 'Статус проектирования',
    'independent_object': 'Самостоятельный объект', 'confidence': 'Уверенность',
    'recommended_action': 'Рекомендация', 'reason': 'Обоснование', 'result': 'Оценка',
    'covered': 'Подтверждено', 'missing': 'Не найдено', 'evidence': 'Доказательства',
    'risk_level': 'Уровень риска', 'recommendation': 'Рекомендуемое действие',
}


def _label(value: Any) -> str:
    raw = str(value or '').strip()
    return _RESULT_LABELS.get(raw.lower(), raw or '—')


def _confidence(value: Any) -> str:
    try:
        number = float(value)
        if number <= 1:
            number *= 100
        return f'{number:.0f}%'
    except (TypeError, ValueError):
        return str(value or '—')


def render_ai_result(data: dict[str, Any], *, title: str = 'Результат AI-анализа', compact: bool = False) -> None:
    """Показывает структурированный ответ AI как инженерную карточку, а не как JSON/код."""
    if not isinstance(data, dict):
        st.info(str(data or 'AI не вернул структурированный результат.'))
        return
    st.markdown(f'#### {title}')
    result = data.get('result') or data.get('entity_type') or data.get('recommended_action')
    confidence = data.get('confidence')
    cols = st.columns(2 if confidence is not None else 1)
    with cols[0]:
        st.metric('Предварительный вывод', _label(result))
    if confidence is not None:
        with cols[1]:
            st.metric('Уверенность', _confidence(confidence))
    reason = data.get('reason') or data.get('explanation') or data.get('rationale')
    if reason:
        st.markdown('**Обоснование**')
        st.write(str(reason))
    for key in ('design_status', 'independent_object', 'recommended_action', 'risk_level'):
        if key not in data or data.get(key) in (None, '', []):
            continue
        label = _FIELD_LABELS.get(key, key)
        value = data.get(key)
        if isinstance(value, bool):
            value = 'Да' if value else 'Нет'
        st.markdown(f'**{label}:** {_label(value)}')
    for key, kind in (('covered', 'success'), ('missing', 'warning')):
        values = data.get(key)
        if not values:
            continue
        text = '; '.join(map(str, values)) if isinstance(values, list) else str(values)
        getattr(st, kind)(f"{_FIELD_LABELS[key]}: {text}")
    evidence = data.get('evidence')
    if evidence and not compact:
        with st.expander('Показать использованные доказательства'):
            if isinstance(evidence, list):
                for idx, item in enumerate(evidence, 1):
                    if isinstance(item, dict):
                        doc = item.get('document') or item.get('file') or 'Документ'
                        page = item.get('page') or '—'
                        quote = item.get('quote') or item.get('context') or item.get('value_text') or ''
                        st.markdown(f'**{idx}. {doc}, стр. {page}**')
                        if quote:
                            st.write(quote)
                    else:
                        st.write(f'• {item}')
            else:
                st.write(evidence)


def render_unstructured_ai_text(text: str) -> None:
    """Резервное отображение: обычный текст без блока кода."""
    cleaned = str(text or '').strip().strip('`')
    if not cleaned:
        st.warning('AI вернул пустой ответ.')
        return
    st.markdown('#### Ответ AI')
    st.write(cleaned)
