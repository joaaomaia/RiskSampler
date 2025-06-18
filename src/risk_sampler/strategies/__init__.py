"""Dynamic registry of weighting strategies."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict

import numpy as np
import pandas as pd

StrategyFunc = Callable[
    [pd.DataFrame, dict[str, Any], dict[str, Any], str, str], np.ndarray
]

_REGISTRY: Dict[str, StrategyFunc] = {}


def register(name: str) -> Callable[[StrategyFunc], StrategyFunc]:
    """Decorator to register a strategy under ``name``."""

    def decorator(func: StrategyFunc) -> StrategyFunc:
        _REGISTRY[name] = func
        return func

    return decorator


def get(name: str) -> StrategyFunc:
    return _REGISTRY[name]


def all_strategies() -> Dict[str, StrategyFunc]:
    return dict(_REGISTRY)


def _discover() -> None:
    pkg_path = Path(__file__).resolve().parent
    for file in pkg_path.glob("*.py"):
        if file.stem == "__init__":
            continue
        import_module(f"{__name__}.{file.stem}")


_discover()
