"""Cost-sensitive weighting using EAD and LGD."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from . import register


@register("expected_loss")
def weights(
    df: pd.DataFrame,
    summary: dict[str, Any],
    cfg: dict[str, Any],
    date_col: str,
    target_col: str,
) -> np.ndarray:
    lgd_col = cfg.get("lgd_col")
    ead_col = cfg.get("ead_col")
    if ead_col is None:
        raise ValueError("expected_loss requires 'ead_col'.")
    w = df[ead_col].astype(float)
    if lgd_col:
        w = w * df[lgd_col].astype(float)
    if cfg.get("scale_to_mean", True):
        w = w / w.mean()
    return w.to_numpy()
