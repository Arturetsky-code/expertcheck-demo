from __future__ import annotations

from math import isfinite
from typing import Any, Mapping

from .contracts import VerificationResult25


def _safe(value: Any) -> Any:
    if isinstance(value, float) and not isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_safe(item) for item in value]
    return value


def report_trace_row(result: VerificationResult25) -> dict[str, Any]:
    trace = result.trace
    proof = trace.proof
    evidence_by_id = {item.evidence_id: item for item in trace.evidence}
    binding_by_id = {item.binding_id: item for item in trace.bindings}

    evidence = next((evidence_by_id[item] for item in proof.evidence_ids if item in evidence_by_id), None)
    binding = next((binding_by_id[item] for item in proof.binding_ids if item in binding_by_id), None)

    row = {
        "requirement_id": result.requirement.requirement_id,
        "decision": trace.decision.state.value,
        "reason_code": trace.decision.reason_code or proof.reason_code,
        "trace_id": trace.trace_id or trace.decision.trace_id,
        "proof_id": proof.proof_id,
        "proof_state": proof.state.value,
        "evidence_id": evidence.evidence_id if evidence else "",
        "binding_id": binding.binding_id if binding else "",
        "document": evidence.resolved_document if evidence else "",
        "page": evidence.page if evidence else None,
        "fragment": evidence.fragment if evidence else "",
        "owner_id": binding.owner_id if binding else "",
        "parameter_code": binding.parameter_code if binding else result.requirement.parameter_code,
    }
    return _safe(row)
