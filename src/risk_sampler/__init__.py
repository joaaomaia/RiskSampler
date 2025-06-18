"""RiskSampler package shim
==========================
Temporary adapter while the code base is migrated from the former
package name *sample_weighter* → *risk_sampler*.

This module re-exports `RiskSampler` and wires an alias so that
`import risk_sampler.core` resolves to `sample_weighter.core`.
"""

from importlib import import_module
import sys
from types import ModuleType

# Import the original implementation
_sample_core: ModuleType = import_module("sample_weighter.core")

# Expose the class at top level
RiskSampler = _sample_core.RiskSampler
__all__ = ["RiskSampler"]

# Make `risk_sampler.core` an alias of the original module, so that
# `from risk_sampler.core import RiskSampler` keeps working.
sys.modules.setdefault("risk_sampler.core", _sample_core)
