from __future__ import annotations

import pandas as pd
from typing import Dict, Tuple

class TargetBuilder:
    """
    Constrói targets binários do tipo `EVERxxMhh` e `OVERxxMhh`.

    Definições
    ----------
    EVER : se o contrato atinge ou ultrapassa o limiar de DPD em
           QUALQUER mês dentro da janela *futura* de `horizon` meses.
    OVER : se o contrato esteve acima do limiar de DPD em
           QUALQUER mês na janela *passada* de `horizon` meses
           (incluindo o mês corrente).

    Exemplo:
        EVER90M12 = 1 se, em algum dos próximos 12 meses,
                     `dpd >= 90`.
        OVER30M4  = 1 se, em algum dos últimos 4 meses (corrente
                     incluído), `dpd >= 30`.

    Parameters
    ----------
    id_col   : str
    date_col : str
    dpd_col  : str, default "dpd"
        Coluna numérica com dias-em-atraso (DPD) ou flag binária.
    freq     : {"M","D",...}, default "M"
    mapping  : dict | None
        Dict opcional no formato
        {"NOME_TARGET": ("ever|over", limiar_dpd:int, janela:int)}.
        Se None, usa o conjunto-padrão abaixo.
    """

    _DEFAULT_MAP: Dict[str, Tuple[str, int, int]] = {
        "EVER30M4":  ("ever", 30, 4),
        "EVER60M6":  ("ever", 60, 6),
        "EVER90M12": ("ever", 90, 12),
        "OVER30M4":  ("over", 30, 4),
        "OVER60M6":  ("over", 60, 6),
        "OVER90M12": ("over", 90, 12),
    }

    def __init__(
        self,
        id_col: str,
        date_col: str,
        dpd_col: str = "dpd",
        freq: str = "M",
        mapping: Dict[str, Tuple[str, int, int]] | None = None,
    ):
        self.id_col = id_col
        self.date_col = date_col
        self.dpd_col = dpd_col
        self.freq = freq
        self.mapping = mapping or TargetBuilder._DEFAULT_MAP

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    def _prep_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte date_col para datetime64[ns] consistente."""
        df = df.copy()
        s = df[self.date_col]

        if pd.api.types.is_integer_dtype(s):
            # assume formato yyyymm
            df[self.date_col] = pd.to_datetime(s.astype(str).str.zfill(6), format="%Y%m")
        else:
            df[self.date_col] = pd.to_datetime(s)

        return df.sort_values([self.id_col, self.date_col])

    # --------------------------------------------------------------------- #
    # Público
    # --------------------------------------------------------------------- #
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Devolve cópia de *df* com as colunas-target solicitadas."""
        df = self._prep_dates(df)

        # Pré-cria flags para cada limiar necessário
        thresholds = {thr for _, thr, _ in self.mapping.values()}
        for thr in thresholds:
            flag = f"__dpd_ge_{thr}"
            if flag not in df.columns:
                df[flag] = (df[self.dpd_col] >= thr).astype("int8")

        # Calcula targets por contrato
        for tgt, (kind, thr, horizon) in self.mapping.items():
            flag = f"__dpd_ge_{thr}"

            if kind == "ever":          # look-ahead
                df[tgt] = (
                    df.groupby(self.id_col, group_keys=False)[flag]
                      .transform(lambda s: s[::-1].rolling(horizon, 1).max()[::-1])
                )
            elif kind == "over":        # look-back
                df[tgt] = (
                    df.groupby(self.id_col, group_keys=False)[flag]
                      .transform(lambda s: s.rolling(horizon, 1).max())
                )
            else:
                raise ValueError(f"Tipo desconhecido: {kind!r}")

            df[tgt] = df[tgt].astype("int8")

        # remove helpers
        df.drop(columns=[c for c in df.columns if c.startswith("__dpd_ge_")],
                inplace=True)
        return df
