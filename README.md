# Tech Challenge Fase 1: Case NPS Preditivo

Este repositório é a minha entrega do Tech Challenge da Fase 1 da pós AI Scientist (FIAP).
A ideia central é simples: hoje a empresa só descobre que o cliente ficou insatisfeito
depois que ele responde a pesquisa de NPS. Eu uso os dados operacionais de ~2.500 pedidos
(pedido, logística e atendimento) para entender o que derruba a satisfação e tentar
prever isso antes da pesquisa, dando à operação a chance de agir a tempo.

A análise inteira pode ser reproduzida rodando um único script (`src/run_pipeline.py`).

## Objetivo

A pergunta que guia o trabalho é: quais fatores operacionais mais influenciam a
satisfação do cliente, e como agir de forma proativa antes da pesquisa de NPS?

Para responder, o projeto passa por quatro frentes (que são exatamente os requisitos
do desafio):

1. Entender o problema de negócio e definir a variável-alvo.
2. Fazer uma EDA com foco em negócio, achando os fatores críticos e o ponto de ruptura.
3. Construir modelos preditivos (regressão e classificação) usando só dados operacionais.
4. Comunicar tudo em linguagem executiva (relatório para gestão, slides e roteiro de vídeo).

## Principais resultados

O diagnóstico é duro: a base tem 79% de detratores, 14,8% de neutros e só 6,2% de
promotores, o que dá um NPS de -72,8. Os três fatores que mais andam junto com a
nota são, nesta ordem, o atraso na entrega (correlação -0,60), o número de
reclamações (-0,50) e o número de contatos com o atendimento (-0,35).

O achado que eu mais gostei: o tempo total de entrega praticamente não muda o NPS
(correlação perto de zero), mas o atraso em relação ao prazo prometido é o maior
vilão. Ou seja, cumprir a promessa importa mais do que ser rápido. E existe um ponto
de ruptura claro na faixa de 2 a 3 dias de atraso: aos 2 dias já são 82% de detratores
e, a partir de 3 dias, passa de 90%.

Nos modelos (só com variáveis operacionais):

| Modelo | Para quê | Resultado |
|---|---|---|
| Regressão Linear | estimar a nota de NPS (0 a 10) | R² = 0,545 / MAE = 1,35 |
| Regressão Logística | sinalizar detratores | ROC-AUC = 0,905 / recall = 0,846 |

![Categorias de NPS](reports/figures/02_categorias_nps.png)
![Atraso vs. NPS](reports/figures/04_nps_por_atraso.png)

## Estrutura do repositório

```
tech-challenge-fase1-nps-preditivo/
├── README.md
├── requirements.txt
├── LICENSE
├── data/
│   ├── raw/                       # base original (desafio_nps_fase_1.csv)
│   └── processed/                 # base tratada (gerada pelo pipeline)
├── src/
│   ├── config.py                  # caminhos, listas de features, regra do NPS
│   ├── data_preparation.py        # carga, validação e criação dos alvos
│   ├── eda.py                     # análise exploratória, figuras e resumo
│   ├── modeling.py                # regressão, classificação e avaliação
│   └── run_pipeline.py            # roda tudo de ponta a ponta
├── notebooks/
│   ├── 01_eda.ipynb
│   └── 02_modelagem.ipynb
├── models/                        # modelos .joblib e metrics.json (gerados)
├── reports/
│   ├── figures/                   # gráficos gerados pela EDA
│   ├── eda_summary.json
│   ├── 03_eda_insights.md         # EDA para a gerência (requisito 3)
│   ├── storytelling_slides.html   # apresentação para público não técnico (reveal.js)
│   └── reveal/                    # reveal.js vendorizado (funciona offline)
└── docs/
    ├── 01_entendimento_negocio.md # requisito 1
    ├── 02_definicao_target.md     # requisito 2
    └── 04_estrategia_preditiva.md # requisito 4
```

## Onde cada requisito está

| Requisito | Arquivo |
|---|---|
| 1. Entendimento do negócio | `docs/01_entendimento_negocio.md` |
| 2. Definição da target | `docs/02_definicao_target.md` |
| 3. EDA com foco em negócio | `reports/03_eda_insights.md`, `notebooks/01_eda.ipynb`, `src/eda.py` |
| 4. Modelo preditivo (opcional) | `docs/04_estrategia_preditiva.md`, `notebooks/02_modelagem.ipynb`, `src/modeling.py` |
| Tratamento e preparação | `src/data_preparation.py` |
| Slides (storytelling) | `reports/storytelling_slides.html` |

## A base de dados

O arquivo `data/raw/desafio_nps_fase_1.csv` tem 2.500 pedidos em 19 colunas, sem
valores ausentes e sem linhas duplicadas. O dicionário de dados:

| Coluna | Descrição |
|---|---|
| `customer_id` | Identificador único do cliente |
| `order_id` | Identificador único do pedido |
| `customer_age` | Idade do cliente |
| `customer_region` | Região geográfica do cliente |
| `customer_tenure_months` | Tempo de relacionamento com a empresa (meses) |
| `order_value` | Valor total do pedido |
| `items_quantity` | Quantidade de itens no pedido |
| `discount_value` | Valor de desconto aplicado |
| `payment_installments` | Número de parcelas do pagamento |
| `delivery_time_days` | Tempo total de entrega (dias) |
| `delivery_delay_days` | Dias de atraso na entrega |
| `freight_value` | Valor do frete |
| `delivery_attempts` | Número de tentativas de entrega |
| `customer_service_contacts` | Número de contatos com o atendimento |
| `resolution_time_days` | Tempo para resolução de problemas (dias) |
| `complaints_count` | Número de reclamações registradas |
| `repeat_purchase_30d` | Recompra em até 30 dias (0/1). Não entra no modelo (vazamento) |
| `csat_internal_score` | Score interno de satisfação. Não entra no modelo (proxy) |
| `nps_score` | Variável-alvo: nota de NPS (0 a 10), coletada após a compra |

Sobre a categorização do NPS: como a nota vem com casas decimais, eu arredondo para o
inteiro mais próximo e aplico a régua clássica (0 a 6 Detrator, 7 a 8 Neutro, 9 a 10
Promotor). A regra fica num único lugar, em `src/config.py`.

## Metodologia

Segui o CRISP-DM, que foi a metodologia trabalhada na fase. O mapeamento das fases
para os arquivos do projeto:

| Fase | O que foi feito | Onde |
|---|---|---|
| Business Understanding | Problema de negócio e definição da target | `docs/01`, `docs/02` |
| Data Understanding | EDA com foco em negócio | `src/eda.py`, `reports/03` |
| Data Preparation | Validação, alvos e pré-processamento | `src/data_preparation.py` |
| Modeling | Regressão e classificação, sempre com baseline | `src/modeling.py` |
| Evaluation | MAE/RMSE/R², AUC/recall, matriz de confusão | `models/metrics.json` |
| Deployment | Reflexão de uso prático e monitoramento | `docs/04` |

## Como reproduzir

Pré-requisito: Python 3.10 ou superior (desenvolvi e testei no 3.14).

```bash
git clone <url-do-repositorio>
cd tech-challenge-fase1-nps-preditivo

# ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -r requirements.txt

# roda preparação + EDA + modelagem
python src/run_pipeline.py
```

Esse comando recria, a partir da base bruta, a base tratada em `data/processed/`,
os gráficos em `reports/figures/`, o `reports/eda_summary.json`, os modelos em
`models/` e o `models/metrics.json`.

Para rodar uma etapa por vez:

```bash
python src/data_preparation.py
python src/eda.py
python src/modeling.py
```

Os notebooks são opcionais (precisa do Jupyter, que está no requirements):

```bash
jupyter notebook notebooks/01_eda.ipynb
```

## Algumas decisões que vale comentar

A mais importante foi não usar `repeat_purchase_30d` nem `csat_internal_score` como
preditoras. A primeira só é conhecida 30 dias depois do pedido (ou seja, não existe no
momento em que eu quero prever) e a segunda é outra medida de satisfação, então usá-la
seria meio circular. Para não ficar só no discurso, o `modeling.py` treina uma versão
"com" essas variáveis e mostra que elas inflam as métricas (AUC sobe de 0,898 para
0,944 e o R² de 0,548 para 0,645). É ganho que não se sustenta na prática.

Além disso: sempre comparo os modelos com um baseline ingênuo (importante porque 79%
da base já é detratora, então acertar não é difícil), uso Pipeline do scikit-learn
para o pré-processamento andar junto com o modelo, e quando dois modelos empatam fico
com o mais simples e fácil de explicar.

## Limitações

A base é sintética, então os padrões precisam ser confirmados com dados reais antes de
qualquer decisão cara. Correlação não é causa: o ideal é validar as ações com teste
A/B. E o modelo serve para priorizar e apoiar a decisão, não para substituir o
julgamento das áreas. Em produção, valeria acompanhar o NPS previsto contra o
realizado e retreinar de tempos em tempos.

## Autoria

Kevin Barreto da Silva, RM374637. FIAP POSTECH, AI Scientist, Fase 1.

## Licença

MIT. Veja o arquivo `LICENSE`.
