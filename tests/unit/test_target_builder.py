import pandas as pd
import pytest

from risk_sampler.builders import TargetBuilder


def make_df():
    # deliberately unsorted vintages
    return pd.DataFrame({
        "id": [1] * 5,
        "date": [202005, 202001, 202003, 202004, 202002],
        "dpd": [0, 0, 60, 0, 0],
    })


def test_ever_over_basic():
    df = make_df()
    tb = TargetBuilder(
        id_col="id",
        date_col="date",
        dpd_col="dpd",
        targets=["EVER30M4", "OVER30M4"],
    )
    out = tb.transform(df)

    expected_dates = pd.to_datetime(
        ["2020-01-01", "2020-02-01", "2020-03-01", "2020-04-01", "2020-05-01"]
    )
    assert out["date"].tolist() == list(expected_dates)
    assert out["EVER30M4"].tolist() == [1, 1, 1, 0, 0]
    assert out["OVER30M4"].tolist() == [0, 0, 1, 1, 1]


def test_unknown_target_raises():
    with pytest.raises(ValueError):
        TargetBuilder("id", "date", targets=["MISSING"])
