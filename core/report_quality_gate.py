from __future__ import annotations

from typing import Any


def validate_review_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate report metrics before they become management conclusions."""
    issues: list[str] = []
    domains = plan.get("domains") or {}
    checked_domains = 0
    for code in ("assignment", "normative", "checklist"):
        summary = domains.get(code) or {}
        if not summary:
            issues.append(f"Отсутствует сводка контура {code}.")
            continue
        checked_domains += 1
        total = int(summary.get("total") or 0)
        verified = int(summary.get("verified_ok") or summary.get("confirmed") or 0)
        findings = int(summary.get("project_findings") or summary.get("issue") or 0)
        review = int(summary.get("review_questions") or summary.get("review") or 0)
        limitations = int(summary.get("system_limitations") or summary.get("system_limitation") or 0)
        informational = int(summary.get("informational") or 0)
        completed = int(summary.get("completed") or 0)
        if completed != verified + findings:
            issues.append(f"{code}: completed не равен confirmed + findings.")
        if total != verified + findings + review + limitations + informational:
            issues.append(f"{code}: сумма классов результатов не равна total.")
        expected = round(100 * completed / max(1, total), 1)
        actual = round(float(summary.get("automatic_coverage_pct", summary.get("coverage_pct", 0)) or 0), 1)
        if actual != expected:
            issues.append(f"{code}: покрытие {actual}% не соответствует {completed}/{total} ({expected}%).")

    for item in plan.get("items") or []:
        status = str(item.get("status") or "").lower()
        title = str(item.get("title") or item.get("plan_id") or "проверка")[:100]
        if "предварительно" in status and item.get("verification_kind") == "VERIFIED_OK":
            issues.append(f"Предварительный результат ошибочно подтверждён: {title}.")
        if item.get("verification_kind") == "VERIFIED_OK" and item.get("adversarial_state") == "BLOCKED":
            issues.append(f"Заблокированный adversarial gate результат остался подтверждённым: {title}.")

    return {
        "status": "PASSED" if not issues and checked_domains == 3 else "FAILED",
        "issues": issues,
        "checked_domains": checked_domains,
        "checks": len(plan.get("items") or []),
    }

