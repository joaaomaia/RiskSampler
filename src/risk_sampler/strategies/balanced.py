"""Class balancing strategy."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from . import register


@register("balanced")
def weights(
    df: pd.DataFrame,
    summary: dict[str, Any],
    cfg: dict[str, Any],
    date_col: str,
    target_col: str,
) -> np.ndarray:
    p = summary["global_er"]
    y = df[target_col].to_numpy()
    return np.where(y == 1, 0.5 / p, 0.5 / (1.0 - p))
