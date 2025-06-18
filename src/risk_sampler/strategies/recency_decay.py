"""Exponential decay favouring recent vintages."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from . import register


@register("recency_decay")
def weights(
    df: pd.DataFrame,
    summary: dict[str, Any],
    cfg: dict[str, Any],
    date_col: str,
    target_col: str,
) -> np.ndarray:
    lam = summary["recency_lambda"]
    max_vint = max(summary["vintage_sizes"].keys())
    delta = max_vint.ordinal - df["_vintage"].map(lambda p: p.ordinal)
    return np.exp(-lam * delta)
