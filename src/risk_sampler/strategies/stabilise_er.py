"""Equalise event-rate across vintages."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from . import register


@register("stabilise_er")
def weights(
    df: pd.DataFrame,
    summary: dict[str, Any],
    cfg: dict[str, Any],
    date_col: str,
    target_col: str,
) -> np.ndarray:
    target_er = cfg.get("target_er", summary["global_er"])
    er = summary["vintage_er"]
    mapping_pos = {v: target_er / max(1e-12, er_v) for v, er_v in er.items()}
    mapping_neg = {
        v: (1.0 - target_er) / max(1e-12, 1.0 - er_v) for v, er_v in er.items()
    }
    vint = df["_vintage"]
    y = df[target_col]
    return np.where(
        y == 1, vint.map(mapping_pos).to_numpy(), vint.map(mapping_neg).to_numpy()
    )
