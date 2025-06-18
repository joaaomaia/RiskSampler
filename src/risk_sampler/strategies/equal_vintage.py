"""Equal contribution per vintage."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from . import register


@register("equal_vintage")
def weights(
    df: pd.DataFrame,
    summary: dict[str, Any],
    cfg: dict[str, Any],
    date_col: str,
    target_col: str,
) -> np.ndarray:
    sizes = summary["vintage_sizes"]
    k = len(sizes)
    n_tot = summary["n_obs"]
    factor = {v: n_tot / (k * n) for v, n in sizes.items()}
    return df["_vintage"].map(factor).to_numpy()
