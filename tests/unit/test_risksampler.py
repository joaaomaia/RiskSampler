import numpy as np
import pandas as pd
import pytest

from risk_sampler.core import RiskSampler


@pytest.fixture()
def df_simple():
    """Synthetic dataframe with 2 vintages and known event‑rate."""
    n1, n2 = 70, 30
    vint1 = pd.Series([202401] * n1, name="vint")
    vint2 = pd.Series([202402] * n2, name="vint")
    y = pd.Series(([1] * 20) + ([0] * 80), name="bad")  # ER = 0.20
    df = pd.DataFrame({"vint": pd.concat([vint1, vint2], ignore_index=True), "bad": y})
    return df.sample(frac=1.0, random_state=42).reset_index(drop=True)  # shuffle rows


# --------------------------------------------------------------------- #
# Balanced strategy                                                     #
# --------------------------------------------------------------------- #

def test_balanced_weights(df_simple):
    rs = RiskSampler(date_col="vint", target_col="bad", strategies={"balanced": {}})
    w = rs.fit_transform(df_simple)

    # Expected raw weights
    w_pos = 0.5 / 0.20  # 2.5
    w_neg = 0.5 / 0.80  # 0.625
    assert pytest.approx(w.mean(), rel=1e-12) == 1.0, "Mean should be 1 after normalise"
    assert set(np.round(w.unique(), 3)) == {round(w_pos, 3), round(w_neg, 3)}


# --------------------------------------------------------------------- #
# Equal‑vintage strategy                                                #
# --------------------------------------------------------------------- #

def test_equal_vintage(df_simple):
    rs = RiskSampler(date_col="vint", target_col="bad", strategies={"equal_vintage": {}})
    w = rs.fit_transform(df_simple)
    # Factors should be 0.7143 and 1.6667 as per docstring
    factors = set(np.round(w.unique(), 4))
    assert factors == {0.7143, 1.6667}
    assert pytest.approx(w.mean(), rel=1e-12) == 1.0


# --------------------------------------------------------------------- #
# Combo strategy (sanity)                                               #
# --------------------------------------------------------------------- #

def test_combo_positive(df_simple):
    strategies = {
        "balanced": {},
        "equal_vintage": {},
        "stabilise_er": {"target_er": 0.18},
        "recency_decay": {"half_life": 6},
        "combo": {"order": [
            "balanced",
            "equal_vintage",
            "stabilise_er",
            "recency_decay",
        ]},
    }
    rs = RiskSampler(date_col="vint", target_col="bad", strategies=strategies)
    w = rs.fit_transform(df_simple)
    # Basic properties
    assert (w > 0).all(), "Weights must be strictly positive"
    assert pytest.approx(w.mean(), rel=1e-12) == 1.0, "Normalised mean must be 1"


# --------------------------------------------------------------------- #
# Expected‑loss strategy                                                #
# --------------------------------------------------------------------- #

def test_expected_loss():
    df = pd.DataFrame(
        {
            "vint": [202401, 202401, 202402, 202402],
            "bad": [1, 0, 1, 0],
            "ead": [100, 200, 150, 250],
            "lgd": [0.5, 0.6, 0.4, 0.7],
        }
    )
    rs = RiskSampler(
        date_col="vint",
        target_col="bad",
        strategies={
            "expected_loss": {"ead_col": "ead", "lgd_col": "lgd", "scale_to_mean": True}
        },
    )
    w = rs.fit_transform(df)
    # After scaling to mean 1, mean exactly 1
    assert pytest.approx(w.mean(), rel=1e-12) == 1.0
    # Check proportional to lgd*ead
    raw = df["ead"] * df["lgd"]
    scaled = raw / raw.mean()
    assert np.allclose(np.sort(w.values), np.sort(scaled.values))


# --------------------------------------------------------------------- #
# Cap functionality                                                     #
# --------------------------------------------------------------------- #

def test_cap_quantile(df_simple):
    rs = RiskSampler(
        date_col="vint",
        target_col="bad",
        strategies={"balanced": {}},
        cap=0.50,  # 50th percentile cap
    )
    w = rs.fit_transform(df_simple)
    # Max should be <= median of uncapped weights (which is 0.625)
    assert w.max() <= 0.625
