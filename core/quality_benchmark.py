from __future__ import annotations

from collections import Counter
from typing import Any

LABELS = {"TP", "FP", "FN", "ABSTAIN_OK", "UNSUPPORTED"}


def benchmark_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate manually curated golden-project quality annotations.

    This module intentionally does not auto-label findings. A specialist marks
    cases after comparing ExpertCheck output with the source project; the engine
    then reports precision/recall and abstention quality across releases.
    """
    labels=[str(r.get("quality_label") or "").upper() for r in rows]
    counts=Counter(x for x in labels if x in LABELS)
    tp,fp,fn=counts["TP"],counts["FP"],counts["FN"]
    precision=tp/max(1,tp+fp)
    recall=tp/max(1,tp+fn)
    f1=(2*precision*recall/max(1e-12,precision+recall)) if (precision+recall) else 0.0
    total=sum(counts.values())
    return {
        "total_reviewed":total,
        "true_positive":tp,
        "false_positive":fp,
        "false_negative":fn,
        "correct_abstention":counts["ABSTAIN_OK"],
        "unsupported":counts["UNSUPPORTED"],
        "precision_pct":round(precision*100,1),
        "recall_pct":round(recall*100,1),
        "f1_pct":round(f1*100,1),
        "false_positive_rate_pct":round(fp/max(1,tp+fp)*100,1),
    }


def empty_annotation(finding_id: str, finding_type: str, project_id: str = "") -> dict[str, Any]:
    return {
        "project_id":project_id,
        "finding_id":finding_id,
        "finding_type":finding_type,
        "quality_label":"",
        "specialist_comment":"",
        "source_reference":"",
        "release":"",
    }
