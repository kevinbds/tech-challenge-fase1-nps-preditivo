"""Roda o projeto inteiro de ponta a ponta: preparacao -> EDA -> modelagem.

E o comando unico de reproducao citado no README (python src/run_pipeline.py). Recria a
base tratada, as figuras, o eda_summary.json, os modelos e o metrics.json a partir da base
bruta.
"""
from __future__ import annotations

import time

import data_preparation
import eda
import modeling

def main():
    """Executa as tres etapas em ordem e imprime o tempo total e as saidas geradas."""
    inicio = time.time()
    print("\n>>> [1/3] DATA PREPARATION\n")
    data_preparation.prepare(save=True, verbose=True)

    print("\n>>> [2/3] ANALISE EXPLORATORIA (EDA)\n")
    eda.run()

    print("\n>>> [3/3] MODELAGEM E AVALIACAO\n")
    modeling.run()

    print(f"\nPipeline concluido em {time.time() - inicio:.1f}s.")
    print("Saidas: data/processed/, reports/figures/, reports/eda_summary.json, "
          "models/*.joblib, models/metrics.json")

if __name__ == "__main__":
    main()
