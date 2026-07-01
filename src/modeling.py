"""Modelagem preditiva: regressao e classificacao (fases Modeling e Evaluation do CRISP-DM).

Preve o NPS antes da pesquisa usando so dados operacionais. Treina uma regressao (estimar
a nota) e uma classificacao (sinalizar detrator), sempre contra um baseline ingenuo, salva
os modelos (.joblib), as figuras e o models/metrics.json, e ainda demonstra na pratica por
que as variaveis de vazamento/proxy ficam de fora.
"""
from __future__ import annotations

import json
import warnings

import config
import joblib
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data_preparation import load_processed
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (GradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.exceptions import ConvergenceWarning
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                             confusion_matrix, f1_score, mean_absolute_error,
                             precision_score, r2_score, recall_score,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Silencio so o ruido conhecido de nomes de features do sklearn ao prever com DataFrame.
# NAO uso um filtro global de UserWarning: ConvergenceWarning herda de UserWarning, e
# esconde-lo mascararia uma eventual nao-convergencia da regressao logistica -- que e
# justamente o aviso que a gente quer continuar vendo. Por isso deixo o ruido de fora
# por mensagem e reforco que o ConvergenceWarning permaneca visivel.
warnings.filterwarnings("ignore", message=".*valid feature names.*")
warnings.filterwarnings("default", category=ConvergenceWarning)

config.apply_plot_style(plt)  # tema escuro alinhado ao deck

def _rmse(y_true, y_pred) -> float:
    """RMSE com fallback de versao: root_mean_squared_error so existe em sklearn>=1.4."""
    try:
        from sklearn.metrics import root_mean_squared_error
        return float(root_mean_squared_error(y_true, y_pred))
    except ImportError:
        from sklearn.metrics import mean_squared_error
        return float(mean_squared_error(y_true, y_pred) ** 0.5)

def build_preprocessor(numeric, categorical) -> ColumnTransformer:
    """Pre-processador: padroniza as numericas e faz one-hot na regiao.

    Vai dentro do Pipeline junto com o modelo, entao o scaler e ajustado so no treino
    (dentro de cada fold do cross-val tambem), o que evita vazamento entre treino e teste.
    """
    return ColumnTransformer([
        ("num", StandardScaler(), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), categorical),
    ])

def get_split(df: pd.DataFrame, features):
    """Divide treino/teste uma unica vez para regressao e classificacao.

    Estratifico por is_detrator para manter a mesma proporcao de detratores nos dois lados
    (a base e desbalanceada, 79% detratores) e fixo random_state para o resultado ser
    reproduzivel. Como o split e o mesmo para os dois alvos, a comparacao fica justa.
    """
    X = df[features].copy()
    y_reg = df[config.TARGET_REGRESSION].copy()
    y_clf = df[config.COL_IS_DETRATOR].copy()
    return train_test_split(
        X, y_reg, y_clf,
        test_size=config.TEST_SIZE,
        random_state=config.RANDOM_STATE,
        stratify=y_clf,
    )

def run_regression(pre, Xtr, Xte, ytr, yte) -> tuple[Pipeline, dict]:
    """Treina e compara modelos de regressao (nota de NPS) e escolhe o de maior R2.

    Sempre inclui um baseline (media) para provar que existe ganho real. Devolve o melhor
    Pipeline ja treinado e um dict com as metricas de todos, o cross-val do melhor e o
    grafico previsto vs. real.
    """
    modelos = {
        "Baseline (media)": DummyRegressor(strategy="mean"),
        "Regressao Linear": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=300, random_state=config.RANDOM_STATE, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(
            random_state=config.RANDOM_STATE),
    }
    resultados = {}
    melhor_nome, melhor_pipe, melhor_r2 = None, None, -np.inf
    for nome, est in modelos.items():
        pipe = Pipeline([("pre", pre), ("model", est)])
        pipe.fit(Xtr, ytr)
        pred = pipe.predict(Xte)
        m = {
            "MAE": round(float(mean_absolute_error(yte, pred)), 3),
            "RMSE": round(_rmse(yte, pred), 3),
            "R2": round(float(r2_score(yte, pred)), 3),
        }
        resultados[nome] = m
        # Criterio de escolha na regressao: maior R2 no teste.
        if m["R2"] > melhor_r2:
            melhor_nome, melhor_pipe, melhor_r2 = nome, pipe, m["R2"]

    cv = cross_val_score(melhor_pipe, Xtr, ytr, cv=5, scoring="r2")
    saida = {
        "alvo": "nps_score (continuo, 0-10)",
        "modelos": resultados,
        "melhor_modelo": melhor_nome,
        "cv_r2_media": round(float(cv.mean()), 3),
        "cv_r2_desvio": round(float(cv.std()), 3),
    }

    pred = melhor_pipe.predict(Xte)
    fig, ax = plt.subplots(figsize=(6.2, 6))
    ax.scatter(yte, pred, alpha=0.35, s=18, color=config.PLOT_ACCENT, edgecolor="none")
    lims = [0, 10]
    ax.plot(lims, lims, color=config.PLOT_MUTED, ls="--", lw=1.2)
    ax.set_xlim(lims); ax.set_ylim(lims)
    ax.set_xlabel("NPS real"); ax.set_ylabel("NPS previsto pelo modelo")
    ax.set_title(f"Regressão: previsto vs. real ({melhor_nome})\n"
                 f"R2 = {resultados[melhor_nome]['R2']:.2f} | "
                 f"MAE = {resultados[melhor_nome]['MAE']:.2f} pontos")
    fig.savefig(config.FIGURES_DIR / "10_regressao_pred_vs_real.png", bbox_inches="tight")
    plt.close(fig)
    return melhor_pipe, saida

def run_classification(pre, Xtr, Xte, ytr, yte) -> tuple[Pipeline, dict]:
    """Treina e compara classificadores de detrator e escolhe o de maior ROC-AUC.

    Uso class_weight='balanced' porque a base e desbalanceada, e escolho por AUC (nao por
    acuracia, que enganaria com 79% de detratores). Devolve o melhor Pipeline e um dict com
    metricas, matriz de confusao, e gera os graficos de matriz e curva ROC.
    """
    modelos = {
        "Baseline (mais frequente)": DummyClassifier(strategy="most_frequent"),
        "Regressao Logistica": LogisticRegression(
            max_iter=1000, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, random_state=config.RANDOM_STATE,
            class_weight="balanced", n_jobs=-1),
    }
    resultados = {}
    melhor_nome, melhor_pipe, melhor_auc = None, None, -np.inf
    for nome, est in modelos.items():
        pipe = Pipeline([("pre", pre), ("model", est)])
        pipe.fit(Xtr, ytr)
        pred = pipe.predict(Xte)
        try:
            proba = pipe.predict_proba(Xte)[:, 1]
            auc = float(roc_auc_score(yte, proba))
        except (AttributeError, ValueError):
            auc = float("nan")
        # auc == auc so e False quando auc e NaN (NaN != NaN); e o jeito de dizer
        # "se conseguimos calcular a AUC" sem precisar importar math.isnan.
        resultados[nome] = {
            "acuracia": round(float(accuracy_score(yte, pred)), 3),
            "acuracia_balanceada": round(float(balanced_accuracy_score(yte, pred)), 3),
            "precisao_detrator": round(float(precision_score(yte, pred, zero_division=0)), 3),
            "recall_detrator": round(float(recall_score(yte, pred, zero_division=0)), 3),
            "f1_detrator": round(float(f1_score(yte, pred, zero_division=0)), 3),
            "roc_auc": round(auc, 3) if auc == auc else None,
        }
        # Criterio de escolha na classificacao: maior AUC (ignorando modelos sem AUC valida).
        if auc == auc and auc > melhor_auc:
            melhor_nome, melhor_pipe, melhor_auc = nome, pipe, auc

    pred = melhor_pipe.predict(Xte)
    proba = melhor_pipe.predict_proba(Xte)[:, 1]
    cm = confusion_matrix(yte, pred)
    saida = {
        "alvo": "is_detrator (1 = detrator, nota arredondada <= 6)",
        "proporcao_detratores_treino": round(float(ytr.mean()), 3),
        "modelos": resultados,
        "melhor_modelo": melhor_nome,
        "matriz_confusao": {
            "verdadeiro_nao_detrator": int(cm[0, 0]),
            "falso_detrator": int(cm[0, 1]),
            "falso_nao_detrator": int(cm[1, 0]),
            "verdadeiro_detrator": int(cm[1, 1]),
        },
    }

    fig, ax = plt.subplots(figsize=(5.6, 5))
    im = ax.imshow(cm, cmap="Blues")
    labels = ["Não-detrator", "Detrator"]
    ax.set_xticks([0, 1]); ax.set_xticklabels(labels)
    ax.set_yticks([0, 1]); ax.set_yticklabels(labels)
    ax.set_xlabel("Previsto"); ax.set_ylabel("Real")
    thr = cm.max() / 2
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i, j]}", ha="center", va="center",
                    color="white" if cm[i, j] > thr else "black",
                    fontsize=14, fontweight="bold")
    ax.set_title(f"Classificação - matriz de confusão ({melhor_nome})")
    fig.savefig(config.FIGURES_DIR / "11_classificacao_matriz_confusao.png", bbox_inches="tight")
    plt.close(fig)

    fpr, tpr, _ = roc_curve(yte, proba)
    fig, ax = plt.subplots(figsize=(6, 5.4))
    ax.plot(fpr, tpr, color=config.PLOT_ACCENT, lw=2.4,
            label=f"{melhor_nome} (AUC = {melhor_auc:.2f})")
    ax.plot([0, 1], [0, 1], ls="--", color="grey", lw=1)
    ax.set_xlabel("Falsos positivos"); ax.set_ylabel("Verdadeiros positivos")
    ax.set_title("Classificação - curva ROC")
    ax.legend(loc="lower right", frameon=False)
    fig.savefig(config.FIGURES_DIR / "13_curva_roc.png", bbox_inches="tight")
    plt.close(fig)
    return melhor_pipe, saida

def plot_importancia(pipe, Xte, yte, features, titulo, fname, scoring):
    """Importancia por permutacao: quanto a performance cai ao embaralhar cada variavel.

    Prefiro permutacao a coeficientes porque funciona igual para qualquer modelo e mede o
    impacto real na metrica de negocio (aqui, a AUC). Devolve a serie ja ordenada.
    """
    r = permutation_importance(pipe, Xte, yte, n_repeats=10,
                               random_state=config.RANDOM_STATE, scoring=scoring)
    imp = pd.Series(r.importances_mean, index=features).sort_values()
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = [config.NPS_COLORS["Promotor"] if v >= 0 else config.NPS_COLORS["Detrator"] for v in imp.values]
    ax.barh(imp.index, imp.values, color=colors, alpha=0.9)
    ax.set_xlabel("Queda na performance ao embaralhar a variável\n(quanto maior, mais importante)")
    ax.set_title(titulo)
    fig.savefig(config.FIGURES_DIR / fname, bbox_inches="tight")
    plt.close(fig)
    return imp.sort_values(ascending=False).round(4)

def leakage_demo(df, features_op) -> dict:
    """Demonstra o efeito do vazamento: mesma familia de modelo, com e sem as suspeitas.

    Treina duas vezes (so operacional vs. operacional + repeat_purchase_30d + csat) para
    mostrar que incluir as variaveis suspeitas infla AUC e R2. O que importa aqui e o salto,
    nao o numero absoluto -- por isso estes valores-base diferem levemente do modelo de
    referencia (usa Random Forest nas duas colunas e um split proprio).
    """
    feats_vazado = features_op + config.EXCLUDED_FROM_PRIMARY_MODEL
    auc, r2 = {}, {}
    for rotulo, feats in [("operacional", features_op), ("com_vazamento", feats_vazado)]:
        num = [c for c in feats if c in config.OPERATIONAL_NUMERIC
               or c in config.EXCLUDED_FROM_PRIMARY_MODEL]
        cat = [c for c in feats if c in config.OPERATIONAL_CATEGORICAL]
        X = df[feats]
        yc = df[config.COL_IS_DETRATOR]
        Xtr, Xte, ytr, yte = train_test_split(
            X, yc, test_size=config.TEST_SIZE,
            random_state=config.RANDOM_STATE, stratify=yc)
        clf = Pipeline([("pre", build_preprocessor(num, cat)),
                        ("model", RandomForestClassifier(
                            n_estimators=300, random_state=config.RANDOM_STATE,
                            class_weight="balanced", n_jobs=-1))])
        clf.fit(Xtr, ytr)
        auc[rotulo] = round(float(roc_auc_score(yte, clf.predict_proba(Xte)[:, 1])), 3)
        yr = df[config.TARGET_REGRESSION]
        Xtr, Xte, ytr, yte = train_test_split(
            X, yr, test_size=config.TEST_SIZE, random_state=config.RANDOM_STATE)
        reg = Pipeline([("pre", build_preprocessor(num, cat)),
                        ("model", LinearRegression())])
        reg.fit(Xtr, ytr)
        r2[rotulo] = round(float(r2_score(yte, reg.predict(Xte))), 3)
    return {
        "classificacao_auc": auc,
        "regressao_r2": r2,
        "variaveis_suspeitas": config.EXCLUDED_FROM_PRIMARY_MODEL,
        "leitura": ("Incluir as variaveis suspeitas eleva AUC e R2, mas elas nao "
                    "estao disponiveis antes da pesquisa (vazamento) e sao proxies "
                    "de satisfacao (circularidade). Por isso ficam fora do modelo."),
    }

def run() -> dict:
    """Orquestra a modelagem: split, regressao, classificacao, importancia e vazamento.

    Salva os dois modelos (.joblib) e o models/metrics.json, e imprime um resumo. E o que
    o run_pipeline.py chama na etapa 3.
    """
    df = load_processed()
    features = config.OPERATIONAL_FEATURES
    Xtr, Xte, yreg_tr, yreg_te, yclf_tr, yclf_te = get_split(df, features)

    pre_reg = build_preprocessor(config.OPERATIONAL_NUMERIC, config.OPERATIONAL_CATEGORICAL)
    pre_clf = build_preprocessor(config.OPERATIONAL_NUMERIC, config.OPERATIONAL_CATEGORICAL)

    reg_pipe, reg_metrics = run_regression(pre_reg, Xtr, Xte, yreg_tr, yreg_te)
    clf_pipe, clf_metrics = run_classification(pre_clf, Xtr, Xte, yclf_tr, yclf_te)

    imp_clf = plot_importancia(
        clf_pipe, Xte, yclf_te, features,
        "Quais variáveis operacionais mais ajudam a prever Detratores",
        "12_importancia_variaveis.png", scoring="roc_auc")
    clf_metrics["importancia_variaveis"] = imp_clf.to_dict()

    leak = leakage_demo(df, features)

    metrics = {
        "configuracao": {
            "n_treino": int(len(Xtr)),
            "n_teste": int(len(Xte)),
            "test_size": config.TEST_SIZE,
            "random_state": config.RANDOM_STATE,
            "features_usadas": features,
            "features_excluidas": config.EXCLUDED_FROM_PRIMARY_MODEL,
        },
        "regressao": reg_metrics,
        "classificacao": clf_metrics,
        "demonstracao_vazamento": leak,
    }

    joblib.dump(reg_pipe, config.MODELS_DIR / "regressor_nps.joblib")
    joblib.dump(clf_pipe, config.MODELS_DIR / "classifier_detrator.joblib")
    with open(config.METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print("=" * 70)
    print("MODELAGEM - resumo")
    print("=" * 70)
    print(f"Regressao  -> melhor: {reg_metrics['melhor_modelo']} | "
          f"R2={reg_metrics['modelos'][reg_metrics['melhor_modelo']]['R2']} | "
          f"MAE={reg_metrics['modelos'][reg_metrics['melhor_modelo']]['MAE']}")
    cm = clf_metrics["modelos"][clf_metrics["melhor_modelo"]]
    print(f"Classific. -> melhor: {clf_metrics['melhor_modelo']} | "
          f"AUC={cm['roc_auc']} | recall_detrator={cm['recall_detrator']} | "
          f"F1={cm['f1_detrator']}")
    print(f"Vazamento  -> AUC: operacional={leak['classificacao_auc']['operacional']} vs "
          f"com suspeitas={leak['classificacao_auc']['com_vazamento']} | "
          f"R2: operacional={leak['regressao_r2']['operacional']} vs "
          f"com suspeitas={leak['regressao_r2']['com_vazamento']}")
    print(f"\nModelos e metrics.json salvos em {config.MODELS_DIR}")
    return metrics

if __name__ == "__main__":
    run()
