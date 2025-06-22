# RiskSampler

Ferramentas de amostragem e preparacão de dados para modelos de PD.

## Exemplos de Uso

### Pesos Balanceados

```python
import pandas as pd
from risk_sampler import RiskSampler

df = pd.DataFrame({
    "vint": [202401, 202401, 202402, 202402],
    "bad": [1, 0, 1, 0],
})

rs = RiskSampler(date_col="vint", target_col="bad", strategies={"balanced": {}})
weights = rs.fit_transform(df)
```

### Igualar Vintages

```python
rs = RiskSampler(date_col="vint", target_col="bad", strategies={"equal_vintage": {}})
weights = rs.fit_transform(df)
```

### Combinação de Estratégias

```python
strategies = {
    "balanced": {},
    "equal_vintage": {},
    "stabilise_er": {"target_er": 0.15},
    "recency_decay": {"half_life": 6},
    "combo": {
        "order": ["balanced", "equal_vintage", "stabilise_er", "recency_decay"]
    },
}
rs = RiskSampler(date_col="vint", target_col="bad", strategies=strategies)
weights = rs.fit_transform(df)
```

### Peso por Perda Esperada

```python
df = pd.DataFrame({
    "vint": [202401, 202401, 202402, 202402],
    "bad": [1, 0, 1, 0],
    "ead": [100, 200, 150, 250],
    "lgd": [0.5, 0.6, 0.4, 0.7],
})
rs = RiskSampler(
    date_col="vint",
    target_col="bad",
    strategies={"expected_loss": {"ead_col": "ead", "lgd_col": "lgd"}},
    cap=None,
)
weights = rs.fit_transform(df)
```

### Decaimento Temporal

```python
rs = RiskSampler(date_col="vint", target_col="bad", strategies={"recency_decay": {"half_life": 3}})
weights = rs.fit_transform(df)
```

### Bootstrap Estratificado

```python
rs = RiskSampler(date_col="vint", target_col="bad", strategies={"stratified_bootstrap": {"random_state": 42}})
weights = rs.fit_transform(df)
```

### Construindo a População Behavior

```python
from risk_sampler.builders import BehaviorPDBuilder

builder = BehaviorPDBuilder(
    id_col="id",
    ref_col="ref",
    default_col="default_flag",
    cure_gap=3,
)
saida = builder.transform(df)
```

### Criando Colunas-Target

```python
from risk_sampler.builders import TargetBuilder

tb = TargetBuilder(id_col="id", date_col="ref", dpd_col="dpd", targets=["EVER90M12"])
resultado = tb.transform(df)
```

### Relatório de Auditoria

```python
report = rs.audit_report(weights)
```

