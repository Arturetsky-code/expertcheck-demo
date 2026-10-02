from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from core.ai_gateway import AIResult, _extract_json


ENGINE_VERSION = "20.0-alpha1-independent-visual-proof"
JUDGE_VERDICTS = {"SUPPORTS", "NOT_PROVEN", "UNREADABLE"}

JUDGE_SYSTEM = (
    "Вы — Visual Judge ExpertCheck. Вы видите РОВНО ОДНУ сохранённую страницу проектной документации. "
    "Проверяйте только пиксели изображения. Название файла, тип листа, текстовый слой, retrieval-маркеры и формулировка вопроса "
    "могут помочь понять, что искать, но сами по себе НЕ являются доказательством. "
    "Для каждого item_id верните SUPPORTS только если обязательный графический элемент реально видим и однозначно идентифицируем "
    "на изображении. Если элемент не найден, неоднозначен или изображение недостаточно читаемо — NOT_PROVEN или UNREADABLE. "
    "Отсутствие визуального доказательства никогда не является автоматическим нарушением. "
    "Верните только JSON по заданной схеме; пояснения — на русском языке."
)

CRITIC_SYSTEM = (
    "Вы — независимый Visual Critic ExpertCheck. Вы получаете то же изображение страницы и только положительные выводы Judge. "
    "Не доверяйте выводу Judge и проверьте изображение заново. accept=true допустимо только если требуемый элемент действительно "
    "виден на изображении и приведённое визуальное основание относится именно к этому элементу. "
    "Текстовая подпись, заголовок листа или метаданные без видимого графического содержания недостаточны. "
    "Если есть сомнение — accept=false. Отрицательный ответ не является нормативным нарушением. "
    "Верните только JSON по заданной схеме; пояснения — на русском языке."
)

JUDGE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["SUPPORTS", "NOT_PROVEN", "UNREADABLE"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "observed_features": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["item_id", "verdict", "confidence", "observed_features", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}

CRITIC_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "reviews": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string"},
                    "accept": {"type": "boolean"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "observed_features": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": ["item_id", "accept", "confidence", "observed_features", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["reviews"],
    "additionalProperties": False,
}


def _norm_float(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _provider_name(result: AIResult | None, fallback: Any = None) -> str:
    if result is not None and str(result.provider or "").strip():
        return str(result.provider).strip()
    return str(getattr(fallback, "name", "") or "").strip()


def _item_base(item: dict[str, Any]) -> str:
    payload = {
        "item_id": str(item.get("item_id") or ""),
        "requirement_id": str(item.get("requirement_id") or ""),
        "element_id": str(item.get("element_id") or ""),
        "label": str(item.get("label") or ""),
        "visual_kind": str(item.get("visual_kind") or ""),
        "review_question": str(item.get("review_question") or ""),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _attempt_key(
    item: dict[str, Any],
    *,
    document: str,
    page: int,
    image_sha256: str,
) -> str:
    raw = "|".join([
        _item_base(item),
        str(document or ""),
        str(int(page or 0)),
        str(image_sha256 or ""),
    ])
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()


def _cache_maps(cache: dict[str, Any] | None) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    by_id = {}
    by_page = {}
    for row in (cache or {}).get("entries") or []:
        if not isinstance(row, dict):
            continue
        value = dict(row)
        cache_id = str(value.get("cache_id") or "")
        document = str(value.get("document") or "")
        try:
            page = int(value.get("page") or 0)
        except (TypeError, ValueError):
            page = 0
        if cache_id:
            by_id[cache_id] = value
        if document and page > 0:
            by_page[(document, page)] = value
    return by_id, by_page


def _candidate_rows(item: dict[str, Any], by_page: dict[tuple[str, int], dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    seen = set()
    for rank, page in enumerate(item.get("candidate_pages") or [], 1):
        if not isinstance(page, dict):
            continue
        document = str(page.get("document") or "")
        try:
            page_no = int(page.get("page") or 0)
        except (TypeError, ValueError):
            page_no = 0
        key = (document, page_no)
        if not document or page_no <= 0 or key in seen:
            continue
        seen.add(key)
        cached = by_page.get(key)
        if not cached:
            continue
        output.append({
            "document": document,
            "page": page_no,
            "rank": rank,
            "cache_id": str(cached.get("cache_id") or ""),
            "image_sha256": str(cached.get("image_sha256") or ""),
            "mime_type": str(cached.get("mime_type") or "image/jpeg"),
            "image_base64": str(cached.get("image_base64") or ""),
            "image_bytes": int(cached.get("image_bytes") or 0),
        })
    return output


def _primary_assignment(page_batches: Iterable[dict[str, Any]] | None) -> dict[str, tuple[str, int]]:
    output = {}
    for batch in page_batches or []:
        if not isinstance(batch, dict):
            continue
        document = str(batch.get("document") or "")
        try:
            page = int(batch.get("page") or 0)
        except (TypeError, ValueError):
            page = 0
        for item in batch.get("items") or []:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("item_id") or "")
            if item_id and document and page > 0:
                output[item_id] = (document, page)
    return output


def _valid_judge_payload(text: str, requested: set[str]) -> bool:
    parsed = _extract_json(text)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
        return False
    seen = set()
    for row in parsed.get("items") or []:
        if not isinstance(row, dict):
            return False
        item_id = str(row.get("item_id") or "")
        verdict = str(row.get("verdict") or "").upper()
        if item_id not in requested or item_id in seen or verdict not in JUDGE_VERDICTS:
            return False
        if not isinstance(row.get("observed_features"), list):
            return False
        seen.add(item_id)
    return seen == requested


def _valid_critic_payload(text: str, requested: set[str]) -> bool:
    parsed = _extract_json(text)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("reviews"), list):
        return False
    seen = set()
    for row in parsed.get("reviews") or []:
        if not isinstance(row, dict):
            return False
        item_id = str(row.get("item_id") or "")
        if item_id not in requested or item_id in seen or not isinstance(row.get("accept"), bool):
            return False
        if not isinstance(row.get("observed_features"), list):
            return False
        seen.add(item_id)
    return seen == requested


def _call_visual(
    provider: Any,
    *,
    prompt: str,
    image_base64: str,
    mime_type: str,
    system: str,
    validator: Any,
    json_schema: dict[str, Any],
) -> AIResult:
    if provider is None:
        return AIResult(False, "Не настроен", error="Vision-провайдер не настроен.", status_code=412)
    generate_validated = getattr(provider, "generate_vision_validated", None)
    if not callable(generate_validated):
        return AIResult(
            False,
            str(getattr(provider, "name", "") or "AI"),
            error="Провайдер не реализует визуальный JSON-контракт ExpertCheck.",
            status_code=412,
        )
    try:
        return generate_validated(
            prompt,
            image_base64,
            mime_type,
            system,
            validator,
            json_schema,
        )
    except Exception as exc:
        return AIResult(
            False,
            str(getattr(provider, "name", "") or "AI"),
            error=f"{type(exc).__name__}: {exc}",
            status_code=0,
        )


def _judge_rows(result: AIResult) -> dict[str, dict[str, Any]]:
    parsed = _extract_json(result.text) if result.ok else None
    if not isinstance(parsed, dict):
        return {}
    return {
        str(row.get("item_id") or ""): dict(row)
        for row in (parsed.get("items") or [])
        if isinstance(row, dict) and str(row.get("item_id") or "")
    }


def _critic_rows(result: AIResult) -> dict[str, dict[str, Any]]:
    parsed = _extract_json(result.text) if result.ok else None
    if not isinstance(parsed, dict):
        return {}
    return {
        str(row.get("item_id") or ""): dict(row)
        for row in (parsed.get("reviews") or [])
        if isinstance(row, dict) and str(row.get("item_id") or "")
    }


def run_normative_visual_proof(
    visual_item_queue: list[dict[str, Any]] | None,
    *,
    page_batches: list[dict[str, Any]] | None,
    visual_cache: dict[str, Any] | None,
    judge_provider: Any,
    critic_provider: Any,
    limit_batches: int = 4,
    checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one resumable Visual Proof wave.

    Positive promotion requires the same cached page to be accepted by two
    actually different providers. A negative/uncertain vision answer never
    becomes PROJECT_FINDING; the next cached candidate is tried on a later wave.
    """
    queue = [dict(row) for row in (visual_item_queue or []) if isinstance(row, dict)]
    checkpoint = dict(checkpoint or {})
    previous_decisions = {
        str(key): dict(value)
        for key, value in (checkpoint.get("decisions") or {}).items()
        if isinstance(value, dict)
    }
    attempts = {
        str(key): [str(value) for value in values if str(value)]
        for key, values in (checkpoint.get("attempted_candidate_keys") or {}).items()
        if isinstance(values, list)
    }
    _, by_page = _cache_maps(visual_cache)
    primary = _primary_assignment(page_batches)
    item_by_id = {
        str(item.get("item_id") or ""): item
        for item in queue
        if str(item.get("item_id") or "")
    }

    decisions: dict[str, dict[str, Any]] = {}
    confirmed = set()
    for item_id, item in item_by_id.items():
        previous = previous_decisions.get(item_id)
        if not previous or str(previous.get("state") or "") != "VISUALLY_CONFIRMED":
            continue
        document = str(previous.get("document") or "")
        try:
            page = int(previous.get("page") or 0)
        except (TypeError, ValueError):
            page = 0
        cached = by_page.get((document, page))
        if not cached:
            continue
        expected = _attempt_key(
            item,
            document=document,
            page=page,
            image_sha256=str(cached.get("image_sha256") or ""),
        )
        if expected == str(previous.get("attempt_key") or ""):
            decisions[item_id] = dict(previous)
            confirmed.add(item_id)

    choice_rows = []
    exhausted = set()
    for item_id, item in item_by_id.items():
        if item_id in confirmed:
            continue
        candidates = _candidate_rows(item, by_page)
        if not candidates:
            exhausted.add(item_id)
            continue
        preferred = primary.get(item_id)
        candidates.sort(key=lambda row: (
            0 if preferred == (row["document"], row["page"]) else 1,
            int(row.get("rank") or 99),
            row["document"],
            row["page"],
        ))
        attempted = set(attempts.get(item_id) or [])
        selected = None
        for candidate in candidates:
            key = _attempt_key(
                item,
                document=candidate["document"],
                page=candidate["page"],
                image_sha256=candidate["image_sha256"],
            )
            if key not in attempted:
                selected = {**candidate, "attempt_key": key}
                break
        if selected is None:
            exhausted.add(item_id)
            continue
        choice_rows.append({
            "item_id": item_id,
            "item": item,
            **selected,
        })

    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in choice_rows:
        grouped.setdefault((row["document"], row["page"]), []).append(row)
    ordered_groups = sorted(
        grouped.items(),
        key=lambda pair: (
            -len(pair[1]),
            min(int(row.get("rank") or 99) for row in pair[1]),
            pair[0][0],
            pair[0][1],
        ),
    )[:max(0, int(limit_batches or 0))]

    provider_errors = []
    batch_audit = []
    processed_batch_count = 0
    newly_confirmed = 0

    for (document, page), rows in ordered_groups:
        cached = by_page.get((document, page)) or {}
        image_base64 = str(cached.get("image_base64") or "")
        mime_type = str(cached.get("mime_type") or "image/jpeg")
        if not image_base64:
            provider_errors.append(f"{document}, стр. {page}: кэш изображения пуст.")
            continue
        requested = {row["item_id"] for row in rows}
        judge_payload = {
            "task": "visual_evidence_judge",
            "document": document,
            "page": page,
            "image_sha256": str(cached.get("image_sha256") or ""),
            "items": [{
                "item_id": row["item_id"],
                "requirement_id": row["item"].get("requirement_id") or "",
                "element": row["item"].get("label") or "",
                "topic": row["item"].get("topic") or "",
                "question": row["item"].get("review_question") or "",
            } for row in rows],
        }
        judge_result = _call_visual(
            judge_provider,
            prompt=json.dumps(judge_payload, ensure_ascii=False, separators=(",", ":")),
            image_base64=image_base64,
            mime_type=mime_type,
            system=JUDGE_SYSTEM,
            validator=lambda text, requested=requested: _valid_judge_payload(text, requested),
            json_schema=JUDGE_JSON_SCHEMA,
        )
        if not judge_result.ok:
            provider_errors.append(
                f"Judge {document}, стр. {page}: {judge_result.error or 'visual-запрос не выполнен'}"
            )
            batch_audit.append({
                "document": document, "page": page, "state": "JUDGE_FAILED",
                "judge_provider": _provider_name(judge_result, judge_provider),
                "error": judge_result.error or "",
            })
            continue

        judge_rows = _judge_rows(judge_result)
        support_ids = {
            item_id for item_id, row in judge_rows.items()
            if str(row.get("verdict") or "").upper() == "SUPPORTS"
        }
        critic_result = None
        critic_rows = {}
        if support_ids:
            critic_payload = {
                "task": "visual_evidence_critic",
                "document": document,
                "page": page,
                "image_sha256": str(cached.get("image_sha256") or ""),
                "judge_provider": _provider_name(judge_result, judge_provider),
                "items": [{
                    "item_id": item_id,
                    "element": item_by_id[item_id].get("label") or "",
                    "question": item_by_id[item_id].get("review_question") or "",
                    "judge_decision": judge_rows[item_id],
                } for item_id in sorted(support_ids)],
            }
            critic_result = _call_visual(
                critic_provider,
                prompt=json.dumps(critic_payload, ensure_ascii=False, separators=(",", ":")),
                image_base64=image_base64,
                mime_type=mime_type,
                system=CRITIC_SYSTEM,
                validator=lambda text, requested=support_ids: _valid_critic_payload(text, requested),
                json_schema=CRITIC_JSON_SCHEMA,
            )
            if critic_result.ok:
                critic_rows = _critic_rows(critic_result)
            else:
                provider_errors.append(
                    f"Critic {document}, стр. {page}: {critic_result.error or 'visual-запрос не выполнен'}"
                )

        actual_judge = _provider_name(judge_result, judge_provider)
        actual_critic = _provider_name(critic_result, critic_provider) if critic_result else ""
        independent = bool(actual_judge and actual_critic and actual_judge != actual_critic)
        processed_batch_count += 1

        for source in rows:
            item_id = source["item_id"]
            judge = judge_rows.get(item_id) or {}
            verdict = str(judge.get("verdict") or "NOT_PROVEN").upper()
            critic = critic_rows.get(item_id) or {}
            judge_conf = _norm_float(judge.get("confidence"))
            critic_conf = _norm_float(critic.get("confidence"))
            critic_accept = critic.get("accept") is True
            positive = bool(
                verdict == "SUPPORTS"
                and judge_conf >= 0.78
                and critic_accept
                and critic_conf >= 0.78
                and independent
            )

            critic_retryable = bool(
                verdict == "SUPPORTS"
                and (critic_result is None or not critic_result.ok)
            )
            if not critic_retryable:
                attempts.setdefault(item_id, [])
                if source["attempt_key"] not in attempts[item_id]:
                    attempts[item_id].append(source["attempt_key"])

            if positive:
                state = "VISUALLY_CONFIRMED"
                confirmed.add(item_id)
                newly_confirmed += 1
                reason = (
                    "Графический элемент подтверждён на сохранённой странице двумя независимыми "
                    "vision-провайдерами и прошёл программный контроль привязки к изображению."
                )
            elif critic_retryable:
                state = "RETRY_SAME_PAGE"
                reason = "Judge увидел элемент, но независимый Critic не завершил проверку; страница остаётся доступной для повтора."
            else:
                candidate_keys = {
                    _attempt_key(
                        item_by_id[item_id],
                        document=candidate["document"],
                        page=candidate["page"],
                        image_sha256=candidate["image_sha256"],
                    )
                    for candidate in _candidate_rows(item_by_id[item_id], by_page)
                }
                remaining = candidate_keys - set(attempts.get(item_id) or [])
                state = "FALLBACK_REQUIRED" if remaining else "REVIEW_QUESTION"
                if verdict == "UNREADABLE":
                    reason = "Изображение недостаточно читаемо для доказательства."
                elif verdict != "SUPPORTS":
                    reason = "На этой странице Visual Judge не получил достаточного положительного доказательства."
                elif not independent:
                    reason = "Положительные ответы не образуют независимый консенсус разных провайдеров."
                else:
                    reason = "Положительный вывод Judge не прошёл независимый Visual Critic/code gate."
                if remaining:
                    reason += " Будет использован следующий сохранённый лист-кандидат."
                else:
                    reason += " Автоматическое нарушение не формируется; вопрос остаётся специалисту."

            decisions[item_id] = {
                "item_id": item_id,
                "requirement_id": source["item"].get("requirement_id") or "",
                "element_id": source["item"].get("element_id") or "",
                "label": source["item"].get("label") or "",
                "state": state,
                "document": document,
                "page": page,
                "cache_id": str(cached.get("cache_id") or ""),
                "image_sha256": str(cached.get("image_sha256") or ""),
                "attempt_key": source["attempt_key"],
                "judge_verdict": verdict,
                "judge_confidence": judge_conf,
                "judge_provider": actual_judge,
                "judge_model": str(judge_result.model or ""),
                "judge_observed_features": list(judge.get("observed_features") or []),
                "judge_reason": str(judge.get("reason") or ""),
                "critic_accept": critic_accept if critic else None,
                "critic_confidence": critic_conf if critic else 0.0,
                "critic_provider": actual_critic,
                "critic_model": str((critic_result.model if critic_result else "") or ""),
                "critic_observed_features": list(critic.get("observed_features") or []),
                "critic_reason": str(critic.get("reason") or ""),
                "independent": independent,
                "reason": reason,
            }

        batch_audit.append({
            "document": document,
            "page": page,
            "state": "COMPLETED",
            "items": sorted(requested),
            "judge_provider": actual_judge,
            "judge_model": str(judge_result.model or ""),
            "critic_provider": actual_critic,
            "critic_model": str((critic_result.model if critic_result else "") or ""),
            "independent": independent,
        })

    for item_id in exhausted:
        if item_id in confirmed:
            continue
        item = item_by_id[item_id]
        decisions[item_id] = {
            **dict(previous_decisions.get(item_id) or {}),
            "item_id": item_id,
            "requirement_id": item.get("requirement_id") or "",
            "element_id": item.get("element_id") or "",
            "label": item.get("label") or "",
            "state": "REVIEW_QUESTION",
            "reason": "Все сохранённые листы-кандидаты исчерпаны либо недоступны. Автоматическое нарушение не формируется; требуется специалист.",
        }

    pending_ids = [item_id for item_id in item_by_id if item_id not in confirmed]
    fallback_required = sum(
        1 for item_id in pending_ids
        if str((decisions.get(item_id) or {}).get("state") or "") == "FALLBACK_REQUIRED"
    )
    review_questions = sum(
        1 for item_id in pending_ids
        if str((decisions.get(item_id) or {}).get("state") or "") == "REVIEW_QUESTION"
    )
    return {
        "version": ENGINE_VERSION,
        "decisions": decisions,
        "attempted_candidate_keys": attempts,
        "queue_total": len(queue),
        "confirmed_total": len(confirmed),
        "newly_confirmed": newly_confirmed,
        "pending_total": len(pending_ids),
        "fallback_required": fallback_required,
        "review_questions": review_questions,
        "selected_batches": len(ordered_groups),
        "processed_batches": processed_batch_count,
        "provider_errors": list(dict.fromkeys(provider_errors)),
        "batch_audit": batch_audit,
        "guardrail": (
            "Visual proof может автоматически подтверждать только положительное наличие графического элемента "
            "при независимом Judge/Critic consensus. NOT_PROVEN/UNREADABLE никогда не создают PROJECT_FINDING."
        ),
    }


def apply_normative_visual_proof(
    proof_result: dict[str, Any],
    visual_checkpoint: dict[str, Any] | None,
    visual_cache: dict[str, Any] | None,
) -> dict[str, Any]:
    result = dict(proof_result or {})
    rows = [dict(row) for row in (result.get("rows") or []) if isinstance(row, dict)]
    checkpoint = dict(visual_checkpoint or {})
    decisions = {
        str(key): dict(value)
        for key, value in (checkpoint.get("decisions") or {}).items()
        if isinstance(value, dict) and str(value.get("state") or "") == "VISUALLY_CONFIRMED"
    }
    _, by_page = _cache_maps(visual_cache)
    queue = [
        dict(item) for item in (result.get("visual_item_queue") or [])
        if isinstance(item, dict)
    ]
    item_by_id = {
        str(item.get("item_id") or ""): item
        for item in queue
        if str(item.get("item_id") or "")
    }
    accepted = {}
    accepted_by_element: dict[tuple[str, str], dict[str, Any]] = {}
    stale = 0
    for item_id, decision in decisions.items():
        item = item_by_id.get(item_id)
        if not item:
            continue
        document = str(decision.get("document") or "")
        try:
            page = int(decision.get("page") or 0)
        except (TypeError, ValueError):
            page = 0
        cached = by_page.get((document, page))
        if not cached:
            stale += 1
            continue
        expected = _attempt_key(
            item,
            document=document,
            page=page,
            image_sha256=str(cached.get("image_sha256") or ""),
        )
        if expected != str(decision.get("attempt_key") or ""):
            stale += 1
            continue
        accepted[item_id] = decision
        key = (
            str(decision.get("requirement_id") or item.get("requirement_id") or ""),
            str(decision.get("element_id") or item.get("element_id") or ""),
        )
        if all(key):
            accepted_by_element[key] = decision

    confirmed_requirements = set()
    evidence_by_requirement: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        requirement_id = str(row.get("requirement_id") or "")
        if str(row.get("proof_state") or "") != "VISUAL_PROOF_REQUIRED":
            continue
        preflight = dict(row.get("visual_preflight") or {})
        elements = []
        visual_pending = []
        visual_total = 0
        for element in preflight.get("elements") or []:
            if not isinstance(element, dict):
                continue
            current = dict(element)
            if str(current.get("verification_mode") or "VISUAL_CONTENT").upper() == "VISUAL_CONTENT":
                visual_total += 1
                element_id = str(current.get("id") or "")
                item_id = f"NORM-VIS-ITEM-{requirement_id}-{element_id}"
                decision = (
                    accepted.get(item_id)
                    or accepted_by_element.get((requirement_id, element_id))
                )
                if decision:
                    current["proof_status"] = "VISUAL_CONFIRMED"
                    current["visual_ai_proof"] = dict(decision)
                    evidence_by_requirement.setdefault(requirement_id, []).append(dict(decision))
                else:
                    visual_pending.append(str(current.get("label") or current.get("id") or ""))
            elements.append(current)
        preflight["elements"] = elements
        preflight["visual_review_required_count"] = len(visual_pending)
        preflight["remaining_visual_labels"] = visual_pending
        row["visual_preflight"] = preflight

        structural_pending = int(preflight.get("structural_review_required_count") or 0)
        if visual_total > 0 and not visual_pending and structural_pending == 0:
            evidence = evidence_by_requirement.get(requirement_id) or []
            row["kind"] = "VERIFIED_OK"
            row["state"] = "Подтверждено"
            row["proof_state"] = "INDEPENDENT_VISUAL_PROOF"
            row["reason_code"] = "NORMATIVE_VISUAL_PROOF_CONFIRMED"
            row["reason"] = (
                "Все обязательные элементы графического содержания подтверждены на сохранённых страницах "
                "независимыми Visual Judge и Visual Critic; структурная часть контракта также закрыта."
            )
            row["visual_ai_proof"] = evidence
            if evidence:
                first = evidence[0]
                row["evidence_document"] = first.get("document") or row.get("evidence_document") or ""
                row["evidence_page"] = first.get("page")
                row["evidence_fragment"] = "; ".join(
                    str(value) for value in (first.get("judge_observed_features") or []) if str(value)
                )[:1000]
            confirmed_requirements.add(requirement_id)

    remaining_items = [
        item for item in queue
        if str(item.get("item_id") or "") not in accepted
    ]
    remaining_requirement_ids = {
        str(item.get("requirement_id") or "")
        for item in remaining_items
        if str(item.get("requirement_id") or "")
    }
    result["rows"] = rows
    result["visual_item_queue"] = remaining_items
    result["visual_item_queue_total"] = len(remaining_items)
    result["visual_item_queue_addressed"] = sum(
        item.get("localization_source") == "ELEMENT_ADDRESS"
        for item in remaining_items
    )
    result["visual_item_queue_sheet_fallback"] = sum(
        item.get("localization_source") == "CONTRACT_SHEET_FALLBACK"
        for item in remaining_items
    )
    result["visual_item_queue_unresolved"] = sum(
        item.get("localization_source") == "UNRESOLVED"
        for item in remaining_items
    )
    result["visual_queue"] = [
        packet for packet in (result.get("visual_queue") or [])
        if str(packet.get("requirement_id") or "") in remaining_requirement_ids
    ]
    result["visual_queue_total"] = len(result["visual_queue"])
    result["visual_proof_applied"] = len(accepted)
    result["visual_contracts_confirmed"] = len(confirmed_requirements)
    result["visual_proof_stale"] = stale > 0
    result["visual_proof_summary"] = {
        "version": checkpoint.get("version") or "",
        "confirmed_total": int(checkpoint.get("confirmed_total") or 0),
        "pending_total": int(checkpoint.get("pending_total") or 0),
        "fallback_required": int(checkpoint.get("fallback_required") or 0),
        "review_questions": int(checkpoint.get("review_questions") or 0),
        "provider_errors": list(checkpoint.get("provider_errors") or []),
        "applied_items": len(accepted),
        "stale_items": stale,
    }
    return result
