from __future__ import annotations

"""Make the 18.5 owner-contract checkpoint migration one-shot.

The original continuation repair intentionally reopens an old ``OTHER_ENTITY``
Judge response when a restored SITE_SPECIFIC requirement no longer requires
standalone owner identity.  That is a migration action, not a permanent queue
rule.  Re-running it on every page render can delete a fresh Judge response and
leave one packet pending forever.

This patch records completion in the project checkpoint.  Clearing/replacing
the checkpoint (new project, fingerprint change, semantic-engine migration)
naturally makes the migration eligible again.
"""

from typing import Any

from . import semantic_continuation as continuation

PATCH_VERSION = "18.5.3-owner-contract-revalidation-once-v1"
_MARKER_KEY = "_owner_contract_revalidation_version"
_RESULT_KEY = "_owner_contract_revalidation_last_reopened"
_INSTALLED = False
_ORIGINAL_INVALIDATOR = continuation._invalidate_nonrequired_owner_other_entity_checkpoint


def invalidate_owner_contract_once(
    doc: dict[str, Any], checkpoint: dict[str, Any] | None,
) -> int:
    """Run the legacy OTHER_ENTITY reopening migration at most once/checkpoint."""
    if not isinstance(checkpoint, dict):
        return 0
    if str(checkpoint.get(_MARKER_KEY) or "") == PATCH_VERSION:
        return 0

    reopened = int(_ORIGINAL_INVALIDATOR(doc, checkpoint) or 0)
    checkpoint[_MARKER_KEY] = PATCH_VERSION
    checkpoint[_RESULT_KEY] = reopened
    return reopened


def install_owner_revalidation_once_patch() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    continuation._invalidate_nonrequired_owner_other_entity_checkpoint = invalidate_owner_contract_once
    _INSTALLED = True


__all__ = [
    "PATCH_VERSION",
    "invalidate_owner_contract_once",
    "install_owner_revalidation_once_patch",
]
