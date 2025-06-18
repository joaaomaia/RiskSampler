"""Bootstrap with undersampling of majority class."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from . import register


@register("stratified_bootstrap")
def weights(
    df: pd.DataFrame,
    summary: dict[str, Any],
    cfg: dict[str, Any],
    date_col: str,
    target_col: str,
) -> np.ndarray:
    rng = np.random.default_rng(cfg.get("random_state"))
    y = df[target_col].to_numpy()
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return np.ones(len(df))
    pos_is_majority = n_pos > n_neg
    maj_mask = y == (1 if pos_is_majority else 0)
    min_mask = ~maj_mask
    n_majority = n_pos if pos_is_majority else n_neg
    n_minority = n_neg if pos_is_majority else n_pos
    p_keep = n_minority / n_majority
    weights = np.zeros(len(df), dtype=float)
    weights[min_mask] = 1.0
    rand = rng.random(maj_mask.sum())
    keep_idx = np.where(maj_mask)[0][rand < p_keep]
    weights[keep_idx] = 1.0 / p_keep
    return weights
