"""risk_sampler package
=====================
Exports the :class:`RiskSampler <risk_sampler.core.RiskSampler>` class and
ensures that imports such as ``from risk_sampler.core import RiskSampler``
work in *src-layout* projects **without** requiring an editable install.
"""

from importlib import import_module
from types import ModuleType
import sys

# Public re-export -----------------------------------------------------------
from .core import RiskSampler  # noqa: F401

__all__: list[str] = ["RiskSampler"]

# ---------------------------------------------------------------------------
# Add alias `risk_sampler.core` -> actual module object, so that libraries
# that expect the sub-module path import correctly.
# ---------------------------------------------------------------------------
_core: ModuleType = import_module("risk_sampler.core")
sys.modules.setdefault("risk_sampler.core", _core)
