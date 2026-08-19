from __future__ import annotations
import json, re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from .normalization import normalize_text

_YEAR_RE = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")

def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None

def reference_year(reference: str) -> int | None:
    years = [int(x) for x in _YEAR_RE.findall(str(reference or ""))]
    return years[-1] if years else None

class NormativeVerificationEngine:
    def __init__(self, knowledge_root):
        root = Path(knowledge_root)
        try:
            self.registry = json.loads((root / "normative_validity_registry.json").read_text(encoding="utf-8"))
        except Exception:
            self.registry = {"records": []}
        try:
            self.queue_data = json.loads((root / "normative_verification_queue.json").read_text(encoding="utf-8"))
        except Exception:
            self.queue_data = {"queue": [], "summary": {}}
        self.records = list(self.registry.get("records") or [])
        self.by_id = {str(x.get("canonical_id")): x for x in self.records}

    def queue(self, priority: str | None = None, pending_only: bool = False, limit: int = 100):
        rows = list(self.queue_data.get("queue") or [])
        if priority:
            rows = [x for x in rows if x.get("priority") == priority]
        if pending_only:
            rows = [x for x in rows if x.get("verification_state") == "PENDING"]
        return rows[:limit]

    def queue_summary(self):
        return dict(self.queue_data.get("summary") or {})

    def edition_assessment(self, record: dict[str, Any], reference: str, *, as_of_date: str | date | None = None) -> dict[str, Any]:
        if isinstance(as_of_date, str):
            asof = _parse_date(as_of_date)
        elif isinstance(as_of_date, date):
            asof = as_of_date
        else:
            asof = _parse_date(self.registry.get("verification_snapshot_date")) or date.today()
        replacement = str(record.get("replacement") or "")
        replacement_from = _parse_date(record.get("replacement_effective_from"))
        current = str(record.get("verified_revision") or record.get("reference") or "")
        ref_year = reference_year(reference)
        current_year = reference_year(current)
        replacement_year = reference_year(replacement)
        status = str(record.get("status") or "")
        outdated = False
        reason = ""
        if replacement and replacement_from and asof and asof >= replacement_from:
            outdated = True
            reason = f"С {replacement_from.isoformat()} документ заменён: {replacement}."
        elif status in {"Заменён", "Утратил силу"}:
            outdated = True
            reason = f"Ссылка ведёт на документ со статусом «{status}»."
        elif ref_year and current_year and ref_year < current_year and normalize_text(reference) != normalize_text(current):
            reason = f"В проекте указана редакция {ref_year} года; в реестре контролируется редакция {current_year} года."
        return {
            "reference_year": ref_year,
            "current_year": current_year,
            "replacement_year": replacement_year,
            "as_of_date": asof.isoformat() if asof else "",
            "edition_status": "Устаревшая редакция" if outdated else ("Проверить редакцию" if reason else "Редакция не вызывает автоматического предупреждения"),
            "edition_outdated": outdated,
            "edition_reason": reason,
            "current_reference": replacement if outdated and replacement else current,
            "replacement_effective_from": record.get("replacement_effective_from", ""),
        }

    def verification_freshness(self, record: dict[str, Any], max_age_days: int = 180) -> dict[str, Any]:
        checked = _parse_date(record.get("verified_on"))
        snapshot = _parse_date(self.registry.get("verification_snapshot_date")) or date.today()
        if not checked:
            return {"freshness": "Не проверено", "days_since_verification": None, "needs_refresh": True}
        days = max(0, (snapshot - checked).days)
        return {
            "freshness": "Актуальная проверка" if days <= max_age_days else "Требуется повторная проверка",
            "days_since_verification": days,
            "needs_refresh": days > max_age_days,
        }

    def enrich_row(self, row: dict[str, Any], record: dict[str, Any] | None = None, *, as_of_date=None) -> dict[str, Any]:
        out = dict(row)
        rec = record or self.by_id.get(str(row.get("canonical_id") or ""))
        if not rec:
            return out
        out["edition_assessment"] = self.edition_assessment(rec, str(row.get("reference") or rec.get("reference") or ""), as_of_date=as_of_date)
        out["verification_freshness"] = self.verification_freshness(rec)
        out["changes"] = list(rec.get("changes") or [])
        out["verification_evidence"] = list(rec.get("verification_evidence") or [])
        out["verification_method"] = rec.get("verification_method", "")
        return out
