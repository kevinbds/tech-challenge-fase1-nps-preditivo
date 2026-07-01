"""Analise exploratoria com foco em negocio (fase Data Understanding do CRISP-DM).

Gera as figuras de reports/figures/ e um resumo numerico em reports/eda_summary.json.
Cada figura ja vem com um titulo que e a propria conclusao, para o material servir de
apoio a leitura gerencial sem precisar de legenda extra.
"""
from __future__ import annotations

import json

import config
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data_preparation import load_processed

config.apply_plot_style(plt)  # tema escuro alinhado ao deck

def _to_native(obj):
    """Converte tipos do numpy (int64, float64, bool_) para tipos nativos do Python.

    O json.dump nao sabe serializar tipos do numpy; passo esta funcao como default=.
    """
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return round(float(obj), 4)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    raise TypeError(f"Tipo nao serializavel: {type(obj)}")

def group_stats(df: pd.DataFrame, by, dropna: bool = True) -> pd.DataFrame:
    """Resume o NPS por grupo: tamanho, nota media e % de detratores/promotores.

    E a operacao que se repete em quase todo grafico de driver, entao fica centralizada
    aqui. 'by' pode ser o nome de uma coluna ou uma Series ja com as faixas (bins).
    """
    g = df.groupby(by, observed=True).agg(
        n=(config.TARGET_REGRESSION, "size"),
        nps_medio=(config.TARGET_REGRESSION, "mean"),
        pct_detrator=(config.COL_NPS_CATEGORY, lambda s: (s == "Detrator").mean() * 100),
        pct_promotor=(config.COL_NPS_CATEGORY, lambda s: (s == "Promotor").mean() * 100),
    )
    return g.round(2)

def _bucket(df: pd.DataFrame, col: str, bins, labels) -> pd.Series:
    return pd.cut(df[col], bins=bins, labels=labels, include_lowest=True)

def save_fig(fig, name: str):
    path = config.FIGURES_DIR / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path

def _driver_chart(df, col, bins, labels, titulo, xlabel, fname):
    """Grafico padrao de "driver": barras de NPS medio + linha de % de detratores por faixa.

    Usa dois eixos y (nota a esquerda, % de detratores a direita) para mostrar, no mesmo
    quadro, que a nota cai enquanto a proporcao de detratores sobe. Devolve as estatisticas
    da faixa para reaproveitar no resumo em JSON.
    """
    bucket = _bucket(df, col, bins, labels)
    stats = group_stats(df, bucket)
    fig, ax1 = plt.subplots(figsize=(8, 4.6))
    x = np.arange(len(stats))
    ax1.bar(x, stats["nps_medio"], color=config.PLOT_ACCENT, alpha=0.85, label="NPS medio")
    ax1.set_ylabel("NPS médio (0-10)", color=config.PLOT_ACCENT)
    ax1.set_ylim(0, 10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(stats.index.astype(str))
    ax1.set_xlabel(xlabel)
    for i, v in enumerate(stats["nps_medio"]):
        ax1.text(i, v + 0.15, f"{v:.1f}", ha="center", fontsize=9, color=config.PLOT_TXT)
    ax2 = ax1.twinx()
    ax2.plot(x, stats["pct_detrator"], color=config.NPS_COLORS["Detrator"],
             marker="o", lw=2.4, label="% Detratores")
    ax2.set_ylabel("% de Detratores", color=config.NPS_COLORS["Detrator"])
    ax2.set_ylim(0, 105)
    ax2.grid(False)
    for i, v in enumerate(stats["pct_detrator"]):
        ax2.text(i, v + 2.5, f"{v:.0f}%", ha="center", fontsize=9,
                 color=config.NPS_COLORS["Detrator"])
    fig.suptitle(titulo, fontsize=13, fontweight="bold")
    save_fig(fig, fname)
    return stats

def fig_distribuicao_nps(df):
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.hist(df[config.TARGET_REGRESSION], bins=21, color=config.PLOT_ACCENT,
            edgecolor="white", alpha=0.9)
    ax.axvspan(-0.2, 6.5, color=config.NPS_COLORS["Detrator"], alpha=0.07)
    ax.axvspan(6.5, 8.5, color=config.NPS_COLORS["Neutro"], alpha=0.10)
    ax.axvspan(8.5, 10.2, color=config.NPS_COLORS["Promotor"], alpha=0.10)
    ax.axvline(df[config.TARGET_REGRESSION].mean(), color=config.PLOT_MUTED, ls="--", lw=1.5)
    ax.text(df[config.TARGET_REGRESSION].mean() + 0.1, ax.get_ylim()[1] * 0.9,
            f"média = {df[config.TARGET_REGRESSION].mean():.1f}", fontsize=9)
    ax.text(3, ax.get_ylim()[1] * 0.78, "Detratores\n(0-6)", ha="center",
            color=config.NPS_COLORS["Detrator"], fontweight="bold")
    ax.text(7.5, ax.get_ylim()[1] * 0.78, "Neutros\n(7-8)", ha="center",
            color=config.NPS_COLORS["Neutro"], fontweight="bold")
    ax.text(9.5, ax.get_ylim()[1] * 0.78, "Promot.\n(9-10)", ha="center",
            color=config.NPS_COLORS["Promotor"], fontweight="bold")
    ax.set_xlabel("Nota de NPS (0 a 10)")
    ax.set_ylabel("Número de clientes")
    fig.suptitle("As notas se concentram na zona de Detratores", fontsize=13,
                 fontweight="bold")
    save_fig(fig, "01_distribuicao_nps.png")

def fig_categorias(df):
    dist = df[config.COL_NPS_CATEGORY].value_counts().reindex(
        ["Detrator", "Neutro", "Promotor"])
    pct = dist / dist.sum() * 100
    nps_metric = pct["Promotor"] - pct["Detrator"]
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    colors = [config.NPS_COLORS[c] for c in dist.index]
    bars = ax.bar(dist.index, dist.values, color=colors, alpha=0.9)
    for b, p in zip(bars, pct.values):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 15,
                f"{p:.1f}%", ha="center", fontweight="bold")
    ax.set_ylabel("Número de clientes")
    ax.set_ylim(0, dist.max() * 1.18)
    fig.suptitle(f"79% são Detratores  |  NPS = {nps_metric:.1f}",
                 fontsize=13, fontweight="bold")
    save_fig(fig, "02_categorias_nps.png")

def fig_correlacoes(df):
    cols = config.OPERATIONAL_NUMERIC + config.EXCLUDED_FROM_PRIMARY_MODEL
    corr = (df[cols + [config.TARGET_REGRESSION]].corr(numeric_only=True)
            [config.TARGET_REGRESSION].drop(config.TARGET_REGRESSION).sort_values())
    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    colors = []
    for name in corr.index:
        if name in config.EXCLUDED_FROM_PRIMARY_MODEL:
            colors.append(config.PLOT_GREY)
        elif corr[name] < 0:
            colors.append(config.NPS_COLORS["Detrator"])
        else:
            colors.append(config.NPS_COLORS["Promotor"])
    ax.barh(corr.index, corr.values, color=colors, alpha=0.9)
    for i, v in enumerate(corr.values):
        ax.text(v + (0.01 if v >= 0 else -0.01), i, f"{v:.2f}",
                va="center", ha="left" if v >= 0 else "right", fontsize=8.5)
    ax.axvline(0, color=config.PLOT_MUTED, lw=0.8)
    ax.set_xlabel("Correlação com a nota de NPS (Pearson)")
    ax.set_xlim(-0.75, 0.75)
    fig.suptitle("O que se relaciona com a satisfação\n(cinza = excluída do modelo: vazamento/proxy)",
                 fontsize=12.5, fontweight="bold")
    save_fig(fig, "03_correlacoes_drivers.png")

def fig_tempo_vs_atraso(df):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    tb = _bucket(df, "delivery_time_days", [1, 4, 7, 9, 12, 14],
                 ["2-4", "5-7", "8-9", "10-12", "13-14"])
    st = group_stats(df, tb)
    a1.bar(st.index.astype(str), st["nps_medio"], color=config.PLOT_GREY, alpha=0.9)
    for i, v in enumerate(st["nps_medio"]):
        a1.text(i, v + 0.1, f"{v:.1f}", ha="center", fontsize=9)
    a1.set_title("Tempo TOTAL de entrega (dias)")
    a1.set_ylabel("NPS médio (0-10)")
    a1.set_ylim(0, 8)
    db = _bucket(df, "delivery_delay_days", [-0.1, 0, 1, 2, 3, 4, 60],
                 ["0", "1", "2", "3", "4", "5+"])
    sd = group_stats(df, db)
    a2.bar(sd.index.astype(str), sd["nps_medio"],
           color=config.NPS_COLORS["Detrator"], alpha=0.9)
    for i, v in enumerate(sd["nps_medio"]):
        a2.text(i, v + 0.1, f"{v:.1f}", ha="center", fontsize=9)
    a2.set_title("ATRASO vs. prometido (dias)")
    a2.set_ylim(0, 8)
    fig.suptitle("Não é a velocidade, é o atraso: tempo total não muda o NPS; atraso, sim",
                 fontsize=12.5, fontweight="bold")
    save_fig(fig, "07_tempo_vs_atraso.png")

def fig_vazamento_recompra(df):
    comp = (df.groupby("repeat_purchase_30d", observed=True)[config.COL_NPS_CATEGORY]
            .value_counts(normalize=True).unstack() * 100).round(1)
    comp = comp.reindex(columns=["Detrator", "Neutro", "Promotor"]).fillna(0)
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    bottom = np.zeros(len(comp))
    labels_x = ["Sem recompra (0)", "Houve recompra (1)"]
    for cat in ["Detrator", "Neutro", "Promotor"]:
        vals = comp[cat].values
        ax.bar(labels_x, vals, bottom=bottom, color=config.NPS_COLORS[cat],
               label=cat, alpha=0.9)
        for i, v in enumerate(vals):
            if v > 3:
                ax.text(i, bottom[i] + v / 2, f"{v:.0f}%", ha="center",
                        color="white", fontweight="bold", fontsize=9)
        bottom += vals
    ax.set_ylabel("Composição (%)")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False)
    fig.suptitle("Vazamento: 'recompra em 30 dias' praticamente entrega a resposta",
                 fontsize=12, fontweight="bold")
    save_fig(fig, "08_vazamento_recompra.png")

def fig_regiao(df):
    st = group_stats(df, "customer_region").sort_values("nps_medio")
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.bar(st.index.astype(str), st["nps_medio"], color=config.PLOT_ACCENT, alpha=0.85)
    for i, v in enumerate(st["nps_medio"]):
        ax.text(i, v + 0.05, f"{v:.2f}", ha="center", fontsize=9)
    ax.set_ylabel("NPS médio (0-10)")
    ax.set_ylim(0, 6)
    fig.suptitle("Região quase não diferencia o NPS (problema é operacional, não geográfico)",
                 fontsize=11.5, fontweight="bold")
    save_fig(fig, "09_nps_por_regiao.png")

def build_summary(df: pd.DataFrame, drivers: dict) -> dict:
    """Monta o dicionario com todos os numeros da EDA (vira o eda_summary.json).

    Serve de fonte unica para os textos (README, docs, slides) citarem numeros sem
    precisar reabrir a base. Inclui distribuicao, NPS, correlacoes, viloes, drivers e
    a demonstracao de vazamento do repeat_purchase_30d.
    """
    dist = df[config.COL_NPS_CATEGORY].value_counts()
    pct = (df[config.COL_NPS_CATEGORY].value_counts(normalize=True) * 100).round(1)
    nps_metric = float((df[config.COL_NPS_CATEGORY].eq("Promotor").mean()
                        - df[config.COL_NPS_CATEGORY].eq("Detrator").mean()) * 100)

    cols = config.OPERATIONAL_NUMERIC + config.EXCLUDED_FROM_PRIMARY_MODEL
    corr = (df[cols + [config.TARGET_REGRESSION]].corr(numeric_only=True)
            [config.TARGET_REGRESSION].drop(config.TARGET_REGRESSION)
            .sort_values().round(3))

    leak = (df.groupby("repeat_purchase_30d", observed=True)[config.COL_NPS_CATEGORY]
            .value_counts(normalize=True).unstack().fillna(0) * 100).round(1)

    summary = {
        "dataset": {
            "n_linhas": int(df.shape[0]),
            "n_colunas_originais": 19,
            "valores_ausentes": int(df.isna().sum().sum()),
            "linhas_duplicadas": int(df.duplicated().sum()),
        },
        "nps_score": {
            "media": round(float(df[config.TARGET_REGRESSION].mean()), 2),
            "mediana": round(float(df[config.TARGET_REGRESSION].median()), 2),
            "desvio_padrao": round(float(df[config.TARGET_REGRESSION].std()), 2),
            "minimo": float(df[config.TARGET_REGRESSION].min()),
            "maximo": float(df[config.TARGET_REGRESSION].max()),
        },
        "categorias": {
            "contagem": {k: int(dist.get(k, 0)) for k in ["Detrator", "Neutro", "Promotor"]},
            "percentual": {k: float(pct.get(k, 0)) for k in ["Detrator", "Neutro", "Promotor"]},
            "nps_metric": round(nps_metric, 1),
        },
        "correlacoes_com_nps": corr.to_dict(),
        "principais_viloes": {k: float(corr[k]) for k in corr.index[:3]},
        "delivery_time_vs_delay": {
            "corr_delivery_time_days": float(corr.get("delivery_time_days", float("nan"))),
            "corr_delivery_delay_days": float(corr.get("delivery_delay_days", float("nan"))),
        },
        "drivers": {name: stats.reset_index().to_dict(orient="records")
                    for name, stats in drivers.items()},
        "vazamento_repeat_purchase_30d": leak.to_dict(orient="index"),
        "regras_categoria": {
            "detrator": "nota arredondada 0-6",
            "neutro": "nota arredondada 7-8",
            "promotor": "nota arredondada 9-10",
        },
        "variaveis_excluidas_modelo_primario": {
            "vazamento": config.LEAKAGE_FEATURES,
            "proxy_satisfacao": config.PROXY_FEATURES,
        },
    }
    return summary

def run() -> dict:
    df = load_processed()

    fig_distribuicao_nps(df)
    fig_categorias(df)
    fig_correlacoes(df)
    drivers = {}
    drivers["delivery_delay_days"] = _driver_chart(
        df, "delivery_delay_days", [-0.1, 0, 1, 2, 3, 4, 60], ["0", "1", "2", "3", "4", "5+"],
        "Cada dia de atraso derruba o NPS, ruptura em 2-3 dias",
        "Dias de atraso na entrega", "04_nps_por_atraso.png")
    drivers["complaints_count"] = _driver_chart(
        df, "complaints_count", [-0.1, 0, 1, 2, 3, 60], ["0", "1", "2", "3", "4+"],
        "Reclamações: a virada acontece entre 1 e 2 reclamações",
        "Número de reclamações registradas", "05_nps_por_reclamacoes.png")
    drivers["customer_service_contacts"] = _driver_chart(
        df, "customer_service_contacts", [-0.1, 0, 1, 2, 3, 60], ["0", "1", "2", "3", "4+"],
        "Quanto mais o cliente precisa acionar o atendimento, pior o NPS",
        "Número de contatos com o atendimento", "06_nps_por_contatos.png")
    fig_tempo_vs_atraso(df)
    fig_vazamento_recompra(df)
    fig_regiao(df)

    summary = build_summary(df, drivers)
    with open(config.EDA_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=_to_native)

    n_figs = len(list(config.FIGURES_DIR.glob("*.png")))
    print(f"EDA concluida. {n_figs} figuras salvas em {config.FIGURES_DIR}")
    print(f"Resumo numerico salvo em {config.EDA_SUMMARY_JSON}")
    return summary

if __name__ == "__main__":
    run()
