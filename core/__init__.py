"""ExpertCheck Core 2.1 — цифровая инженерная модель и движки проверки."""

__version__ = "2.1-alpha1"

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
