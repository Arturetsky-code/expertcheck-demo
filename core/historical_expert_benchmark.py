from __future__ import annotations
from typing import Any

def evaluate_findings(known:list[dict[str,Any]]|None, predicted:list[dict[str,Any]]|None)->dict[str,Any]:
    """Lightweight benchmark for known expert remarks. Matching is explicit by benchmark_id or normalized signature."""
    known=known or []; predicted=predicted or []
    def key(x):
        return str(x.get('benchmark_id') or x.get('finding_id') or x.get('signature') or '').strip().lower()
    ks={key(x) for x in known if key(x)}; ps={key(x) for x in predicted if key(x)}
    tp=len(ks & ps); fn=len(ks-ps); fp=len(ps-ks)
    recall=tp/max(1,tp+fn); precision=tp/max(1,tp+fp)
    return {'known':len(ks),'predicted':len(ps),'true_positive':tp,'false_negative':fn,'false_positive':fp,'expert_recall_pct':round(recall*100,1),'finding_precision_pct':round(precision*100,1)}
