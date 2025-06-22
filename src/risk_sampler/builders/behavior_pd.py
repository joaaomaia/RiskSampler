import pandas as pd
import numpy as np


class BehaviorPDBuilder:
    """
    Constrói a população de PD (Behavior), em painel mensal, SEM snapshot.
    
    Premissas
    ---------
    • Apenas meses *performing* entram no dataset final.
    • O primeiro default encerra o spell.
    • Um novo spell só nasce após 'cure_gap' meses seguidos performando.
    
    Parâmetros
    ----------
    id_col       : str  – coluna de identificação do contrato (ex.: 'NroContrato')
    ref_col      : str  – coluna temporal (int yyyymm ou datetime64[ns])
    default_col  : str  – flag mensal de default (1=default no mês, 0=performing)
    target_col   : str | None – coluna-alvo já calculada (ex.: 'TARGET')
    cure_gap     : int  – nº de meses consecutivos performing que definem “cura” (padrão 3)
    freq         : str  – frequência a assumir se ref_col for datetime (padrão 'M')
    """

    def __init__(
        self,
        id_col: str,
        ref_col: str,
        default_col: str,
        target_col: str | None = None,
        cure_gap: int = 3,
        freq: str = "M",
    ):
        self.id_col = id_col
        self.ref_col = ref_col
        self.default_col = default_col
        self.target_col = target_col
        self.cure_gap = cure_gap
        self.freq = freq

    # ------------------------------------------------------------------ #
    # MÉTODO PÚBLICO
    # ------------------------------------------------------------------ #
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Retorna o DataFrame filtrado + colunas auxiliares de spell.

        Várias etapas:
        1. Converte ref_col para pandas Period → coluna interna “_ref”.
        2. Marca linhas performing.
        3. Assina spells por contrato (agrupamento + _assign_spells).
           • include_groups=False silencia o FutureWarning em pandas ≥2.2.
        4. Mantém apenas meses performing já “curados”.
        5. Cria months_elapsed dentro do spell.
        6. Calcula flag censored (1 = nenhum default no spell).
        7. Reorganiza colunas e reinicia índice.
        """
        df = df.copy()
        df = self._prep_time(df)
        df["performing"] = df[self.default_col] == 0

        # Agrupa por contrato e aplica a lógica de spells
        df = (
            df.sort_values([self.id_col, "_ref"])
              .groupby(self.id_col, group_keys=False)
              .apply(self._assign_spells, include_groups=False)  # pandas 2.2+
        )

        # Mantém apenas meses performing aceitos
        df = df[df["keep"]].drop(columns=["keep", "performing", "_ref"])

        # Ordenação dentro do spell
        df["months_elapsed"] = df.groupby("spell_id").cumcount()

        # Flag de censura
        default_flag = (
            df.groupby("spell_id")[self.default_col]
              .max()
              .rename("default_happened")
        )
        df = df.merge(default_flag, left_on="spell_id", right_index=True)
        df["censored"] = (df["default_happened"] == 0).astype(int)
        df = df.drop(columns="default_happened")

        # Ordem final de colunas
        front = [
            self.id_col,
            "spell_id",
            self.ref_col,
            "months_elapsed",
            "censored",
        ]
        if self.target_col:
            front.append(self.target_col)

        ordered = front + [c for c in df.columns if c not in front]
        return df[ordered].reset_index(drop=True)


    # ------------------------------------------------------------------ #
    # MÉTODOS PRIVADOS
    # ------------------------------------------------------------------ #
    def _prep_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte ref_col para pandas Period e ordena."""
        if np.issubdtype(df[self.ref_col].dtype, np.number):
            # int yyyymm → Period
            df["_ref"] = pd.to_datetime(
                df[self.ref_col].astype(str) + "01", format="%Y%m%d"
            ).dt.to_period(self.freq)
        else:
            df["_ref"] = pd.to_datetime(df[self.ref_col]).dt.to_period(self.freq)
        return df

    def _assign_spells(self, g: pd.DataFrame) -> pd.DataFrame:
        """
        Dentro de um contrato, numera spells e decide quais linhas manter.

        Observação:
        Se `include_groups=False` (pandas ≥2.2) remover a coluna de agrupamento,
        recriamos `self.id_col` a partir de `g.name`.
        """
        # Garante a presença da coluna id_col (para compatibilidade futura)
        if self.id_col not in g.columns:
            g[self.id_col] = g.name

        # 1) Início de spell = transição False→True em performing
        start = (~g["performing"].shift(fill_value=False) & g["performing"]).cumsum()
        g["spell_seq"] = np.where(g["performing"], start, np.nan)

        # 2) Regra de cura
        if self.cure_gap > 0:
            consec_perf = (
                g["performing"]
                  .groupby((g["performing"] != g["performing"].shift()).cumsum())
                  .cumcount() + 1
            )
            not_cured = (
                g["performing"]
                & (consec_perf < self.cure_gap)
                & (g[self.default_col].shift(fill_value=0) == 1)
            )
            g.loc[not_cured, "spell_seq"] = np.nan

        # 3) Decide linhas a manter
        g["keep"] = g["performing"] & g["spell_seq"].notna()
        g.loc[g["keep"], "spell_seq"] = g.loc[g["keep"], "spell_seq"].astype(int)

        # 4) Cria identificador único do spell
        g["spell_id"] = (
            g[self.id_col].astype(str)
            + "_"
            + g["spell_seq"].fillna(0).astype(int).astype(str)
        )

        return g