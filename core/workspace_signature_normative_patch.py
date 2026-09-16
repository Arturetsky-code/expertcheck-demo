from __future__ import annotations

import hashlib
import json
from typing import Any


PATCH_VERSION = "18.5.4-normative-proof-persistence-signature"


def _normative_semantic_proof(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the persisted normative semantic proof from the project result.

    ``result`` is intentionally not serialised by the ordinary workspace
    signature because it can contain tens of megabytes of evidence.  The
    normative semantic proof is small and mutable, however, so it needs its own
    compact marker or Streamlit autosave cannot see partial/final proof runs.
    """
    result = payload.get("result")
    if not isinstance(result, (list, tuple)) or not result:
        return {}

    # ExpertCheck stores analysed documents as the first result part.  Search
    # that part defensively instead of relying on one exact document index.
    documents = result[0] if isinstance(result[0], (list, tuple)) else []
    for document in documents:
        if not isinstance(document, dict):
            continue
        proof = document.get("normative_semantic_proof")
        if isinstance(proof, dict) and proof:
            return proof
    return {}


def normative_semantic_proof_digest(payload: dict[str, Any]) -> str:
    proof = _normative_semantic_proof(payload)
    if not proof:
        return ""
    raw = json.dumps(
        proof,
        ensure_ascii=False,
        default=str,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def install_workspace_signature_normative_patch() -> None:
    """Make workspace autosave sensitive to normative semantic proof changes.

    The existing signature remains authoritative for all prior state.  We only
    add a second digest when a normative semantic proof is present, which keeps
    the patch backward compatible and cheap on projects without that proof.
    """
    from . import workspace_store

    original = workspace_store.snapshot_signature
    if getattr(original, "_normative_proof_persistence_patch", False):
        return

    def patched_snapshot_signature(payload: dict[str, Any]) -> str:
        base_signature = original(payload)
        proof_digest = normative_semantic_proof_digest(payload)
        if not proof_digest:
            return base_signature
        raw = f"{base_signature}|{PATCH_VERSION}|{proof_digest}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    patched_snapshot_signature._normative_proof_persistence_patch = True  # type: ignore[attr-defined]
    patched_snapshot_signature._normative_proof_persistence_version = PATCH_VERSION  # type: ignore[attr-defined]
    patched_snapshot_signature._unpatched_snapshot_signature = original  # type: ignore[attr-defined]
    workspace_store.snapshot_signature = patched_snapshot_signature
