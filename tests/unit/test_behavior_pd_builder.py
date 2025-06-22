import pandas as pd
import numpy as np
import pytest

from risk_sampler.builders.behavior_pd import BehaviorPDBuilder


def make_df(refs, defaults, id_col="id", ref_col="ref", default_col="def"):
    """
    Monta um DataFrame de teste com
      - id_col repetido (contrato único ou múltiplos IDs se refs for lista de listas)
      - ref_col como ints ou datetimes
      - default_col conforme defaults
    """
    # Se refs for 2D, desembrulha cada lista como um contrato diferente
    if isinstance(refs[0], (list, np.ndarray)):
        rows = []
        for i, (r, d) in enumerate(zip(refs, defaults), start=1):
            for rv, dv in zip(r, d):
                rows.append({id_col: i, ref_col: rv, default_col: dv})
        return pd.DataFrame(rows)
    else:
        return pd.DataFrame({
            id_col: [1] * len(refs),
            ref_col: refs,
            default_col: defaults
        })


def test_integer_ref_basic_spell():
    # 3 meses, sem default até o último (que será dropado por performing=False)
    df = make_df(
        refs=[202001, 202002, 202003],
        defaults=[0, 0, 1],
        id_col="ID",
        ref_col="AnoMesReferencia",
        default_col="mau_30",
    )
    builder = BehaviorPDBuilder(
        id_col="ID",
        ref_col="AnoMesReferencia",
        default_col="mau_30",
    )
    out = builder.transform(df)

    # só mantém os dois meses que são performing
    assert len(out) == 2

    # meses_elapsed deve ser [0, 1]
    assert out["months_elapsed"].tolist() == [0, 1]

    # censored: o spell não teve default interno → censored=1
    assert out["censored"].tolist() == [1, 1]

    # spell_id único para ambos
    assert out["spell_id"].unique().tolist() == ["1_1"]


def test_datetime_ref_preserva_dtype():
    dates = pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"])
    df = make_df(
        refs=list(dates),
        defaults=[0, 0, 1],
        id_col="C",
        ref_col="date",
        default_col="D",
    )
    builder = BehaviorPDBuilder("C", "date", "D")
    out = builder.transform(df)

    # mantém a coluna 'date' com mesmo dtype datetime64[ns]
    assert pd.api.types.is_datetime64_any_dtype(out["date"].dtype)

    # só os dois primeiros ficam
    assert out["date"].tolist() == dates[:2].tolist()


def test_cure_gap_zero_ignora_cura_gap():
    # default no mês 2, performing no mês 3 → com cure_gap=0 mantém o 3º mês
    df = make_df(
        refs=[202001, 202002, 202003],
        defaults=[0, 1, 0],
        id_col="X",
        ref_col="AnoMesReferencia",
        default_col="df",
    )
    b0 = BehaviorPDBuilder("X", "AnoMesReferencia", "df", cure_gap=0)
    out0 = b0.transform(df)

    # mantém dois performing: mês 1 e mês 3
    assert len(out0) == 2

    # meses_elapsed reinicia em cada spell de comprimento 1 → [0, 0]
    assert out0["months_elapsed"].tolist() == [0, 0]

    # spell_id distintos (novo spell após default)
    assert set(out0["spell_id"]) == {"1_1", "1_2"}


def test_cure_gap_gt0_aplica_cura_gap():
    # mesmo cenário, mas com cure_gap=3 → mês 3 NÃO tem cura suficiente e é dropado
    df = make_df(
        refs=[202001, 202002, 202003],
        defaults=[0, 1, 0],
        id_col="X",
        ref_col="AnoMesReferencia",
        default_col="df",
    )
    b3 = BehaviorPDBuilder("X", "AnoMesReferencia", "df", cure_gap=3)
    out3 = b3.transform(df)

    # só mantém o primeiro mês performing
    assert len(out3) == 1
    assert out3["months_elapsed"].tolist() == [0]


def test_multiplos_ids_independentes():
    # dois contratos com default no segundo mês cada
    refs = [
        [202001, 202002],
        [202001, 202002],
    ]
    defs = [
        [0, 1],
        [0, 1],
    ]
    df = make_df(
        refs=refs,
        defaults=defs,
        id_col="ID",
        ref_col="AnoMesReferencia",
        default_col="def",
    )
    b = BehaviorPDBuilder("ID", "AnoMesReferencia", "def", cure_gap=0)
    out = b.transform(df)

    # espera 1 linha por contrato (o 1º performing de cada)
    assert out.shape[0] == 2
    # IDs presentes
    assert set(out["ID"]) == {1, 2}
    # spell_id de cada deve começar em 1_1 e 2_1
    assert set(out["spell_id"]) == {"1_1", "2_1"}
