"""
RiskSampler – Ferramentas para amostragem e modelagem de risco.
Public API: exporta as classes centrais do pacote.
"""

from importlib.metadata import version, PackageNotFoundError

from .core import RiskSampler
from .builders import BehaviorPDBuilder  # noqa: F401

from .target_builder import TargetBuilder

# versão do pacote (dev-mode ou instalado via wheel)
try:
    __version__ = version("risk_sampler")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__: list[str] = [
    "RiskSampler",
    "BehaviorPDBuilder",
    "TargetBuilder"
]
