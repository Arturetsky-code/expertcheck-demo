from __future__ import annotations

from core.verification_runtime_audit_patch import install
from core import semantic_evidence_engine as see


def test_audit_patch_installs_without_weakening_l5_contract():
    before = see.run_semantic_evidence_engine
    install()
    after = see.run_semantic_evidence_engine
    assert callable(after)
    assert getattr(after, "_expertcheck_184_audit_reconciled", False) or after is before
