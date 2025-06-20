"""
==================================
Core implementation of the SampleWeighter class.

The class is intended for binary‑classification PD Behaviour models and
implements multiple weighting strategies that can be combined.

Strategies implemented
----------------------
balanced          – class balancing
equal_vintage     – equal contribution per vintage
stabilise_er      – equalise event‑rate across vintages
recency_decay     – exponential decay favouring recent vintages
expected_loss     – cost‑sensitive weighting (LGD × EAD)
combo             – ordered composition of the above

"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd

from . import strategies

__all__ = ["RiskSampler"]


class RiskSampler:
    """Compute *sample_weight* vectors for behavioural PD models.

    Parameters
    ----------
    id_cols : str | Sequence[str] | None, default None
        Identifier columns (optional, only kept for logging / auditing).
    date_col : str
        Column name with vintage / reference date.
        - int ``yyyymm``  (202401)
        - datetime64[ns]
        - str  ``"yyyymm"``
    target_col : str
        Name of the binary target column (0 / 1).
    strategies : dict[str, dict[str, Any]] | None, default None
        Dictionary where **key** is the strategy name and the **value**
        is another dictionary with hyper‑parameters for that strategy.
        Example::

            strategies = {
                "balanced": {},
                "equal_vintage": {},
                "stabilise_er": {"target_er": 0.10},
                "recency_decay": {"half_life": 6},
                "combo": {"order": ["balanced", "equal_vintage",
                                        "stabilise_er", "recency_decay"]},
            }
    normalise : bool, default True
        If *True*, final weights are rescaled to mean == 1.
    cap : float | None, default 0.95
        If float (0 < cap ≤ 1) apply an upper cap at the given quantile
        of the weight distribution. ``None`` disables capping.
    verbose : int, default 0
        0 – silent; 1 – info; 2 – debug.
    """

    _ALLOWED = set(strategies.all_strategies().keys()) | {"combo"}

    def __init__(
        self,
        *,
        id_cols: str | Sequence[str] | None = None,
        date_col: str,
        target_col: str,
        strategies: Dict[str, Dict[str, Any]] | None = None,
        normalise: bool = True,
        cap: float | None = 0.95,
        verbose: int = 0,
    ) -> None:
        self.id_cols = (
            [id_cols] if isinstance(id_cols, str) else list(id_cols) if id_cols else []
        )
        self.date_col = date_col
        self.target_col = target_col
        self.strategies = strategies or {"balanced": {}, "equal_vintage": {}}
        self.normalise = normalise
        self.cap = cap
        self.verbose = verbose

        # internal caches populated on fit
        self._fitted = False
        self.summary_: dict[str, Any] = {}

    # --------------------------------------------------------------------- #
    # Public API                                                             #
    # --------------------------------------------------------------------- #
    def fit(self, df: pd.DataFrame) -> "RiskSampler":
        """Compute dataset‑level statistics required by some strategies."""
        df = df.copy()
        df["_vintage"] = self._to_period(df[self.date_col])

        # basic stats
        self.summary_ = {
            "n_obs": len(df),
            "global_er": df[self.target_col].mean(),
            "vintage_sizes": df["_vintage"].value_counts().to_dict(),
            "vintage_er": df.groupby("_vintage")[self.target_col].mean().to_dict(),
        }

        # pre‑calc recency decay λ if needed
        rd_cfg = self.strategies.get("recency_decay")
        if rd_cfg:
            if "lambda_" in rd_cfg:
                lam = float(rd_cfg["lambda_"])
            else:
                half_life = float(rd_cfg.get("half_life", 6))
                lam = math.log(2) / max(half_life, 1e-6)
            self.summary_["recency_lambda"] = lam

        # nothing else to pre‑compute here
        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.Series:
        """Return a *pd.Series* with sample weights (index aligned to *df*)."""
        if not self._fitted:
            raise RuntimeError("SampleWeighter not fitted. Call .fit() first.")

        if self.verbose >= 1:
            print("[SampleWeighter] Computing weights…")

        df = df.copy()
        df["_vintage"] = self._to_period(df[self.date_col])

        weights = np.ones(len(df), dtype=float)

        # Determine order of application
        order: List[str]
        if "combo" in self.strategies:
            order = list(self.strategies["combo"].get("order", []))
        else:
            order = list(self.strategies.keys())

        for strat in order:
            if strat == "combo":
                continue  # skip meta-strategy
            if strat not in self._ALLOWED:
                raise ValueError(
                    f"Unknown strategy '{strat}'. Allowed: {self._ALLOWED}"
                )
            func = strategies.get(strat)
            cfg = self.strategies.get(strat, {})
            w_part = func(df, self.summary_, cfg, self.date_col, self.target_col)
            weights *= w_part
            if self.verbose >= 2:
                print(f"  · {strat:15s} → mean={w_part.mean():.4f}")
        # ----- post‑processing -----
        if self.cap is not None:
            q = np.quantile(weights, self.cap)
            weights = np.minimum(weights, q)
        if self.normalise:
            weights = weights / weights.mean()

        return pd.Series(weights, index=df.index, name="sample_weight")

    # sklearn‑compat
    def fit_transform(self, df: pd.DataFrame) -> pd.Series:  # noqa: D401
        """Shortcut for *fit* followed by *transform*."""
        return self.fit(df).transform(df)

    def audit_report(self, weights: pd.Series) -> dict[str, Any]:
        """Return basic JSON audit information for *weights*.

        Parameters
        ----------
        weights : pd.Series
            Weights produced by :meth:`transform`.

        Returns
        -------
        dict[str, Any]
            Dictionary with mean weight, KS-test p-value against an
            all-ones baseline and the applied cap quantile.
        """
        from scipy.stats import ks_2samp

        w = weights.to_numpy()
        p_value = ks_2samp(w, np.ones_like(w), alternative="two-sided").pvalue
        return {
            "mean": float(w.mean()),
            "ks_pvalue": float(p_value),
            "cap": None if self.cap is None else float(self.cap),
        }

    # --------------------------------------------------------------------- #
    # Utilities                                                              #
    # --------------------------------------------------------------------- #
    @staticmethod
    def _to_period(s: pd.Series) -> pd.Series:
        """Convert various date formats to ``pandas.Period['M']``."""
        if isinstance(s.dtype, pd.PeriodDtype):
            return s
        if np.issubdtype(s.dtype, np.datetime64):
            return s.dt.to_period("M")
        if np.issubdtype(s.dtype, np.integer):
            return pd.to_datetime(s.astype(str) + "01", format="%Y%m%d").dt.to_period(
                "M"
            )
        # assume str yyyymm
        return pd.to_datetime(s + "01", format="%Y%m%d").dt.to_period("M")
