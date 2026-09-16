"""ExpertCheck Core 2.1 — цифровая инженерная модель и движки проверки."""

__version__ = "20.0-alpha1-dual-run"

from .dem import DigitalEngineeringModel, DEMObject, DEMValue, build_dem
from .validation import ValidationEngine
from .relations import RelationEngine
from .model_quality import calculate_model_quality

__all__ = [
    "DigitalEngineeringModel", "DEMObject", "DEMValue", "build_dem",
    "ValidationEngine", "RelationEngine", "calculate_model_quality",
]

from .object_register_engine import ObjectRegisterEngine, build_registry

from .passport_engine import build_object_passports, passport_summary
from .general_plan_engine import GeneralPlanRegisterEngine, GeneralPlanEntry
from .register_reconciliation import RegisterReconciliationEngine, ReconciledObject, reconcile_register
from .cross_section_verification import qualify_cross_section_verdicts, technology_proof_summary
from .project_profiles import ProjectProfileRegistry, ProjectProfile

from .object_identity import ObjectIdentityEngine, IdentityDecision

# 18.5.2: current rebuilt L4 packet universe is authoritative for the active
# resumable AI queue. Historical ledger totals remain diagnostics only.
from .ai_queue_universe_patch import install_ai_queue_universe_patch

install_ai_queue_universe_patch()

# 18.5.3: reopening legacy OTHER_ENTITY decisions after a contract change is a
# one-shot checkpoint migration. Fresh Judge responses must survive rerenders.
from .owner_revalidation_once_patch import install_owner_revalidation_once_patch

install_owner_revalidation_once_patch()

# 18.5.4: normative semantic proof mutates inside the persisted project result.
# Include a compact proof digest in the workspace rerun signature so partial and
# final Alpha 10 proof runs are autosaved and survive Streamlit reboot.
from .workspace_signature_normative_patch import install_workspace_signature_normative_patch

install_workspace_signature_normative_patch()

# Alpha 10.1.1: provenance shown to the engineer must never contain pandas/JSON
# serialization sentinels such as literal "nan". Patch both the evidence renderer
# and the already-bound project assembly function before Studio imports them.
from .quality_integrity_1011_patch import install_quality_integrity_1011_patch

install_quality_integrity_1011_patch()
