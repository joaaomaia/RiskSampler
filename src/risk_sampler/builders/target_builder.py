from __future__ import annotations

import re
from typing import Dict, Iterable, Tuple
import pandas as pd
from tqdm.auto import tqdm


class TargetBuilder:
    """
    Constrói targets `EVER/OVER-<dpd><U><h>` onde:
        U ∈ {M=meses, Q=trimestres, Y=anos, D=dias}

    Ex.: EVER30Q8 → dpd≥30 em qualquer dos próximos 8 trimestres
    """

    _DEFAULT_MAP: Dict[str, Tuple[str, int, int]] = {
        "EVER30M4":  ("ever", 30, 4),
        "EVER60M6":  ("ever", 60, 6),
        "EVER90M12": ("ever", 90, 12),
        "OVER30M4":  ("over", 30, 4),
        "OVER60M6":  ("over", 60, 6),
        "OVER90M12": ("over", 90, 12),
    }

    _UNIT2MONTH = {"M": 1, "Q": 3, "Y": 12, "D": 1}
    _FREQ2MONTH = {"M": 1, "Q": 3, "Y": 12, "D": 1}

    # ------------------------------------------------------------------ #
    # Init
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        id_col: str,
        date_col: str,
        dpd_col: str = "dpd",
        freq: str = "M",
        mapping: Dict[str, Tuple[str, int, int]] | None = None,
        targets: Iterable[str] | None = None,
        progress: bool = False,
    ):
        self.id_col = id_col
        self.date_col = date_col
        self.dpd_col = dpd_col
        self.freq = freq.upper()
        if self.freq not in self._FREQ2MONTH:
            raise ValueError(f"freq inválido: {freq!r}. Use M, Q, Y ou D.")
        self.progress = progress

        # 1) ponto de partida
        self.mapping: Dict[str, Tuple[str, int, int]] = (
            mapping.copy() if mapping is not None else self._DEFAULT_MAP.copy()
        )

        # 2) se o usuário listou targets explícitos…
        if targets is not None:
            for tgt in targets:
                if tgt not in self.mapping:
                    # parse e adiciona
                    self.mapping[tgt] = self._parse_target_name(tgt)
            # mantém só os solicitados
            self.mapping = {k: v for k, v in self.mapping.items() if k in targets}

        # 3) sanity-check
        if not self.mapping:
            raise ValueError("Nenhum target solicitado/mapeado.")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    _PAT = re.compile(r"^(EVER|OVER)(\d+)([MDQY])(\d+)$", re.I)

    def _parse_target_name(self, name: str) -> Tuple[str, int, int]:
        """
        Converte 'EVER30Q8' → ('ever', 30, 24)  (24 = 8×3 meses)
        Depois ajusta para a frequência base (`freq`).
        """
        m = self._PAT.match(name)
        if not m:
            raise ValueError(
                f"Nome de target inválido: {name!r}. "
                "Use EVER/OVER + <dias> + M/Q/Y/D + <horizonte>."
            )
        kind, thr, unit, h = m.groups()
        kind = kind.lower()
        thr = int(thr)
        h = int(h)
        unit = unit.upper()

        # converte tudo para 'meses'
        unit_months = self._UNIT2MONTH[unit]
        horizon_months = h * unit_months

        # converte para nº de períodos na freq base
        base_months = self._FREQ2MONTH[self.freq]
        if horizon_months % base_months != 0:
            raise ValueError(
                f"Horizonte de {name} ({horizon_months} meses) "
                f"não é múltiplo da frequência base {self.freq}."
            )
        horizon_periods = horizon_months // base_months
        return kind, thr, horizon_periods

    def _prep_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte `date_col` em datetime64[ns] e ordena."""
        df = df.copy()
        s = df[self.date_col]

        if pd.api.types.is_integer_dtype(s):
            df[self.date_col] = pd.to_datetime(
                s.astype(str).str.zfill(6), format="%Y%m"
            )
        else:
            df[self.date_col] = pd.to_datetime(s)

        return df.sort_values([self.id_col, self.date_col])

    # ------------------------------------------------------------------ #
    # Público
    # ------------------------------------------------------------------ #
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Retorna *df* com as colunas-target solicitadas."""
        df = self._prep_dates(df)

        # Flags auxiliares dpd≥limiar
        thresholds = {thr for _, thr, _ in self.mapping.values()}
        for thr in tqdm(thresholds, desc="thresholds", disable=not self.progress):
            flag = f"__dpd_ge_{thr}"
            if flag not in df.columns:
                df[flag] = (df[self.dpd_col] >= thr).astype("int8")

        # Calcula cada target
        for tgt, (kind, thr, horizon) in tqdm(
            self.mapping.items(), desc="targets", disable=not self.progress
        ):
            flag = f"__dpd_ge_{thr}"

            if kind == "ever":  # look-ahead
                df[tgt] = (
                    df.groupby(self.id_col, group_keys=False)[flag]
                    .transform(lambda s: s[::-1].rolling(horizon, 1).max()[::-1])
                )
            elif kind == "over":  # look-back
                df[tgt] = (
                    df.groupby(self.id_col, group_keys=False)[flag]
                    .transform(lambda s: s.rolling(horizon, 1).max())
                )
            else:
                raise ValueError(f"Tipo desconhecido: {kind!r}")

            df[tgt] = df[tgt].astype("int8")

        # remove helpers
        df.drop(columns=[c for c in df.columns if c.startswith("__dpd_ge_")], inplace=True)
        return df
