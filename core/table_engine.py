from __future__ import annotations
from dataclasses import dataclass, asdict
import re

@dataclass
class TableCandidate:
    table_type: str
    score: float
    headers: list[str]
    rows: list[list[str]]
    evidence: list[str]
    def to_dict(self): return asdict(self)

class TableEngine:
    """Lightweight table classifier for PDF text layers; designed for catalog expansion."""
    def __init__(self, catalog: list[dict]):
        self.catalog = catalog

    @staticmethod
    def _lines(text: str) -> list[str]:
        return [re.sub(r"\s+", " ", x).strip() for x in text.splitlines() if x.strip()]

    def detect(self, text: str) -> list[TableCandidate]:
        lines = self._lines(text)
        low = "\n".join(lines).lower().replace("ё", "е")
        result=[]
        for tpl in self.catalog:
            tokens=[x.lower().replace("ё","е") for x in tpl.get("header_tokens",[])]
            hits=[x for x in tokens if x in low]
            score=len(hits)/max(1,len(tokens))
            if score < tpl.get("threshold",0.5):
                continue
            rows=[]
            for i,line in enumerate(lines):
                if re.match(r"^\d+(?:\.\d+)*\s+", line) or any(k in line.lower() for k in tpl.get("row_tokens",[])):
                    rows.append([line])
            result.append(TableCandidate(tpl["id"], round(score,3), hits, rows[:100], [f"найдено заголовков: {len(hits)}"]))
        return sorted(result, key=lambda x:x.score, reverse=True)
