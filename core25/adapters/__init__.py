"""Adapters from stable ExpertCheck cores into the 25.0 contracts."""

from .core20 import adapt_evidence, adapt_requirement

__all__ = ["adapt_evidence", "adapt_requirement"]
