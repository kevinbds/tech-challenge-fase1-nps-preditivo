# 2. Definição da Variável-Alvo (Target)

Aqui o desafio pede entendimento conceitual, não técnico. É a parte em que eu pego o
problema de negócio da seção anterior e traduzo para um alvo que um modelo consiga
aprender, que é a ponte entre Business Understanding e Data Understanding no CRISP-DM.

## Qual variável representa a satisfação do cliente?

A variável-alvo é o `nps_score`, a nota de 0 a 10 que o cliente dá depois da compra.
Ela é a tradução direta da pergunta de recomendação do NPS. A partir dela eu derivo
mais duas, dependendo de como vou modelar:

| Alvo | Tipo | Como é definido | Para quê |
|---|---|---|---|
| `nps_score` | contínuo (0 a 10) | a própria nota | regressão, estimar a nota |
| `nps_category` | categórico | 0 a 6 Detrator, 7 a 8 Neutro, 9 a 10 Promotor | leitura de negócio |
| `is_detrator` | binário (0/1) | 1 quando a nota arredondada é até 6 | classificação, sinalizar risco |

Uma observação de método: como o `nps_score` veio com casas decimais, eu arredondo
para o inteiro mais próximo antes de aplicar a régua clássica do NPS. Essa regra fica
registrada em `src/config.py` e é aplicada igual no projeto inteiro, para não ter
duas definições diferentes circulando.

Seguindo a estrutura de Unidade, Ação e Período que vimos na fase, dá para enunciar o
alvo assim: a probabilidade de um pedido (e o cliente associado a ele) se tornar
detrator ao final da jornada de compra. A unidade é o pedido, a ação é virar detrator
(nota até 6) e o período é o fim da jornada, que é quando a pesquisa seria aplicada.

## Por que ela foi escolhida?

Por alguns motivos. Ela é a métrica oficial de satisfação e lealdade que a empresa já
usa, então está alinhada com a dor e com o que a liderança acompanha. Ela também se
liga direto à decisão que eu quero apoiar, que é agir antes do cliente virar detrator.
E ela permite as duas abordagens que o desafio sugere: a regressão, para estimar a
nota e priorizar por grau de risco, e a classificação, para tomar uma decisão binária
de acionar ou não a operação.

Entre as duas, a `is_detrator` é a mais acionável no dia a dia. Como 79% da base já é
detratora, reduzir esse grupo é a maior alavanca de valor que existe, e uma decisão de
"agir ou não agir" é algo que a operação consegue executar.

## Em que momento da jornada essa informação é coletada?

O `nps_score` é coletado depois do fim da jornada, normalmente numa pesquisa
pós-entrega. Esse ponto é central para o projeto inteiro. Como é um indicador
defasado, ele chega quando a experiência ruim já aconteceu. Por isso a ideia é
prevê-lo a partir de dados operacionais que existem antes da pesquisa, como pedido,
logística e atendimento. O momento da previsão, então, é durante ou ao fim da
jornada, usando só o que já se sabe naquele instante.

## Existe risco de usar essa variável de forma inadequada?

Existe, e alguns merecem atenção.

O mais grave é o vazamento de alvo. Se eu usar como preditora uma variável que só
existe no mesmo momento ou depois da nota, o modelo fica ótimo no papel e inútil na
prática. Na base tem dois casos clássicos. O `repeat_purchase_30d` só é conhecido até
30 dias depois do pedido, e nos dados ele separa quase perfeitamente promotor de
detrator, então prever NPS com ele é basicamente ver a resposta antes. Já o
`csat_internal_score` é outra medida de satisfação, e prever satisfação a partir de
satisfação é circular e não aponta nenhuma alavanca operacional. Por isso os dois
ficam de fora do modelo, e essa decisão está demonstrada com números na parte 4.

Tem ainda o risco de confundir correlação com causa. O modelo mostra associações, mas
agir como se fossem causas exige validação, de preferência um teste A/B, antes de
qualquer decisão cara. Também existe o viés de quem responde a pesquisa, já que esse
grupo pode não representar todos os clientes. Outro risco é perseguir o número sem
tratar a causa: dá para "maquiar" o NPS sem mexer em atraso e reclamação, mas isso
melhora o indicador, não a experiência. Por fim, antes de automatizar qualquer ação
vale checar se o modelo não está penalizando injustamente algum perfil de cliente,
ainda que aqui o perfil tenha peso pequeno.

No geral, a satisfação é representada pelo `nps_score` (e pela sua versão acionável,
o `is_detrator`). Ele é coletado tarde, o que justifica tentar prevê-lo com dados
operacionais, e o cuidado maior é não deixar entrar variável que entrega a resposta.
Esse princípio guia toda a modelagem da parte 4.
