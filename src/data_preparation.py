"""Carga, validacao e preparacao da base (fase Data Preparation do CRISP-DM).

Le a base bruta, roda uns testes de sanidade (nulos, duplicatas, valores fora de faixa),
cria as colunas-alvo derivadas do nps_score e salva a base tratada em data/processed/.
"""
from __future__ import annotations

import config
import pandas as pd

# Faixas plausiveis para as colunas mais sensiveis. Serve so para pegar sujeira obvia
# (ex.: idade negativa, NPS fora de 0-10); nao e um limpador, e um alarme.
EXPECTED_RANGES = {
    "customer_age": (0, 120),
    "nps_score": (0, 10),
    "delivery_delay_days": (0, 60),
    "complaints_count": (0, 50),
    "customer_service_contacts": (0, 50),
    "repeat_purchase_30d": (0, 1),
}

def load_raw() -> pd.DataFrame:
    """Le o CSV bruto de data/raw/. Falha com mensagem clara se o arquivo nao estiver la."""
    if not config.RAW_CSV.exists():
        raise FileNotFoundError(
            f"Base bruta nao encontrada em {config.RAW_CSV}. "
            "Copie 'desafio_nps_fase_1.csv' para data/raw/."
        )
    return pd.read_csv(config.RAW_CSV)

def validate(df: pd.DataFrame) -> dict:
    """Roda os testes de qualidade da base e devolve um relatorio (dict).

    Confere shape, nulos, duplicatas (linhas e ids), presenca das colunas obrigatorias
    e valores fora de faixa. Levanta erro so se faltar coluna essencial; o resto e
    reportado para a gente decidir o que fazer.
    """
    report: dict = {}
    report["n_rows"], report["n_cols"] = df.shape
    report["missing_total"] = int(df.isna().sum().sum())
    report["duplicate_rows"] = int(df.duplicated().sum())
    report["duplicate_customer_id"] = int(df["customer_id"].duplicated().sum())
    report["duplicate_order_id"] = int(df["order_id"].duplicated().sum())

    required = set(
        config.ID_COLS
        + config.OPERATIONAL_FEATURES
        + [config.TARGET_REGRESSION]
        + config.EXCLUDED_FROM_PRIMARY_MODEL
    )
    missing_cols = sorted(required - set(df.columns))
    if missing_cols:
        raise ValueError(f"Colunas obrigatorias ausentes na base: {missing_cols}")

    out_of_range = {}
    for col, (lo, hi) in EXPECTED_RANGES.items():
        if col in df.columns:
            n_bad = int(((df[col] < lo) | (df[col] > hi)).sum())
            if n_bad:
                out_of_range[col] = n_bad
    report["out_of_range"] = out_of_range
    return report

def add_target_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Cria as tres colunas-alvo a partir do nps_score.

    nps_score_int (nota arredondada), nps_category (Detrator/Neutro/Promotor) e
    is_detrator (1/0), que sao os alvos de regressao, leitura de negocio e classificacao.
    """
    df = df.copy()
    df[config.COL_NPS_INT] = config.round_half_up(df[config.TARGET_REGRESSION])
    df[config.COL_NPS_CATEGORY] = config.classify_nps(df[config.COL_NPS_INT])
    df[config.COL_IS_DETRATOR] = (df[config.COL_NPS_INT] <= config.DETRACTOR_MAX).astype(int)
    return df

def prepare(save: bool = True, verbose: bool = True) -> pd.DataFrame:
    """Roda a preparacao de ponta a ponta: carrega, valida, cria alvos e salva.

    Imprime um relatorio de qualidade quando verbose=True e grava a base tratada
    em data/processed/ quando save=True. Devolve o DataFrame ja com as colunas-alvo.
    """
    df = load_raw()
    report = validate(df)
    df = add_target_columns(df)

    if verbose:
        print("=" * 70)
        print("DATA PREPARATION - relatorio de qualidade")
        print("=" * 70)
        print(f"Linhas x Colunas ........: {report['n_rows']} x {report['n_cols']}")
        print(f"Valores ausentes ........: {report['missing_total']}")
        print(f"Linhas duplicadas .......: {report['duplicate_rows']}")
        print(f"customer_id duplicados ..: {report['duplicate_customer_id']}")
        print(f"order_id duplicados .....: {report['duplicate_order_id']}")
        print(f"Valores fora de faixa ...: {report['out_of_range'] or 'nenhum'}")
        dist = df[config.COL_NPS_CATEGORY].value_counts()
        pct = (df[config.COL_NPS_CATEGORY].value_counts(normalize=True) * 100).round(1)
        print("\nDistribuicao de NPS (apos categorizacao):")
        for cat in ["Detrator", "Neutro", "Promotor"]:
            print(f"  {cat:<9}: {int(dist.get(cat, 0)):>5}  ({pct.get(cat, 0):>4}%)")
        nps_metric = (df[config.COL_NPS_CATEGORY].eq("Promotor").mean()
                      - df[config.COL_NPS_CATEGORY].eq("Detrator").mean()) * 100
        print(f"  NPS (=%Promotores - %Detratores): {nps_metric:.1f}")

    if save:
        df.to_csv(config.PROCESSED_CSV, index=False)
        if verbose:
            print(f"\nBase tratada salva em: {config.PROCESSED_CSV}")
    return df

def load_processed() -> pd.DataFrame:
    """Devolve a base tratada; se ainda nao existir, roda prepare() para gera-la.

    E o ponto de entrada usado pela EDA e pela modelagem, para elas nunca dependerem
    da ordem em que os scripts sao chamados.
    """
    if not config.PROCESSED_CSV.exists():
        return prepare(save=True, verbose=False)
    return pd.read_csv(config.PROCESSED_CSV)

if __name__ == "__main__":
    prepare(save=True, verbose=True)
