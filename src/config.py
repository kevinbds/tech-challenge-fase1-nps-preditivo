"""Configuracao central do projeto: caminhos, listas de features e a regra do NPS.

Deixo tudo o que e "verdade unica" aqui (onde ficam os dados, quais colunas entram no
modelo, como categorizar a nota) para nao ter duas definicoes diferentes circulando
pelo pipeline. Qualquer script importa daqui.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

RAW_CSV = RAW_DIR / "desafio_nps_fase_1.csv"
PROCESSED_CSV = PROCESSED_DIR / "nps_processed.csv"
EDA_SUMMARY_JSON = REPORTS_DIR / "eda_summary.json"
METRICS_JSON = MODELS_DIR / "metrics.json"

for _d in (PROCESSED_DIR, MODELS_DIR, REPORTS_DIR, FIGURES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.20

ID_COLS = ["customer_id", "order_id"]

TARGET_REGRESSION = "nps_score"
COL_NPS_INT = "nps_score_int"
COL_NPS_CATEGORY = "nps_category"
COL_IS_DETRATOR = "is_detrator"

OPERATIONAL_NUMERIC = [
    "order_value",
    "items_quantity",
    "discount_value",
    "payment_installments",
    "delivery_time_days",
    "delivery_delay_days",
    "freight_value",
    "delivery_attempts",
    "customer_service_contacts",
    "resolution_time_days",
    "complaints_count",
    "customer_age",
    "customer_tenure_months",
]
OPERATIONAL_CATEGORICAL = ["customer_region"]
OPERATIONAL_FEATURES = OPERATIONAL_NUMERIC + OPERATIONAL_CATEGORICAL

# Duas variaveis que ficam de fora do modelo primario de proposito:
# - repeat_purchase_30d so e conhecida ate 30 dias depois do pedido -> vazamento temporal
#   (nao existe no momento em que queremos prever).
# - csat_internal_score e outra medida de satisfacao -> prever satisfacao com satisfacao
#   e circular e nao aponta nenhuma alavanca operacional.
LEAKAGE_FEATURES = ["repeat_purchase_30d"]
PROXY_FEATURES = ["csat_internal_score"]
EXCLUDED_FROM_PRIMARY_MODEL = LEAKAGE_FEATURES + PROXY_FEATURES

DETRACTOR_MAX = 6
PASSIVE_MAX = 8

def round_half_up(s: pd.Series) -> pd.Series:
    """Arredonda a nota de NPS para o inteiro mais proximo, com 0,5 sempre para cima.

    Uso floor(x + 0,5) de proposito: o round() do Python/numpy faz "banker's rounding"
    (2,5 -> 2), o que deslocaria notas exatas de meio ponto para o lado errado da regua.
    """
    return np.floor(s.astype(float) + 0.5).astype(int)

def classify_nps(nps_int: pd.Series) -> pd.Series:
    """Aplica a regua classica do NPS sobre a nota ja arredondada.

    0 a 6 = Detrator, 7 a 8 = Neutro (passivo), 9 a 10 = Promotor.
    """
    cats = pd.cut(
        nps_int,
        bins=[-1, DETRACTOR_MAX, PASSIVE_MAX, 10],
        labels=["Detrator", "Neutro", "Promotor"],
    )
    return cats.astype("string")

# Cores das categorias de NPS (alinhadas ao deck de storytelling)
NPS_COLORS = {
    "Detrator": "#ff7a85",
    "Neutro": "#ffd166",
    "Promotor": "#2dd4bf",
}

# Paleta e tema escuro dos graficos, para combinar com o storytelling_slides.html
PLOT_BG = "#0c0f19"
PLOT_TXT = "#eef1fb"
PLOT_MUTED = "#9aa6c6"
PLOT_ACCENT = "#8b93f8"
PLOT_GREY = "#586074"
PLOT_EDGE = "#28304a"

def apply_plot_style(plt):
    """Aplica o tema escuro aos graficos (mesma identidade visual do deck)."""
    plt.rcParams.update({
        "figure.dpi": 130, "savefig.dpi": 150, "font.size": 11,
        "text.color": PLOT_TXT,
        "axes.facecolor": PLOT_BG, "figure.facecolor": PLOT_BG, "savefig.facecolor": PLOT_BG,
        "axes.edgecolor": PLOT_EDGE, "axes.labelcolor": PLOT_MUTED,
        "axes.titlecolor": PLOT_TXT, "axes.titlesize": 13, "axes.titleweight": "bold",
        "xtick.color": PLOT_MUTED, "ytick.color": PLOT_MUTED,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#ffffff", "grid.alpha": 0.06,
        "figure.autolayout": True,
    })
