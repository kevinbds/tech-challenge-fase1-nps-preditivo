# 1. Entendimento do Negócio

Esta primeira parte é de raciocínio, não de código. É a fase de Business
Understanding do CRISP-DM, e a proposta do desafio aqui é justamente exercitar o
pensamento analítico antes de abrir qualquer notebook.

## Contexto

A empresa é um e-commerce que cresceu rápido e passou a lidar com muito mais pedidos,
entregas e contatos de clientes. Esse crescimento foi bom para a escala, mas deixou
um problema à mostra: o NPS varia demais entre clientes parecidos. Dois pedidos com
números operacionais semelhantes acabam gerando um promotor e um detrator, e não
estava claro o porquê.

Hoje o NPS só é coletado depois que a compra termina. Na prática, a empresa fica
sempre correndo atrás do prejuízo: quando a nota chega, o cliente já está insatisfeito
e não dá mais para salvar aquela experiência.

Olhando os dados, a situação é pior do que um ajuste fino. Dos 2.500 pedidos da base,
79% são de detratores, 14,8% de neutros e só 6,2% de promotores, o que dá um NPS de
-72,8. Isso não é um cliente ou outro reclamando, é o padrão atual da operação.

## Qual problema de negócio está sendo resolvido?

A dor é que a empresa descobre tarde demais que o cliente ficou insatisfeito. Em
linguagem de negócio, a pergunta é: quais fatores operacionais realmente influenciam
a satisfação, e como agir antes da pesquisa de NPS para melhorar a experiência?

Traduzindo isso para algo acionável, o projeto precisa fazer três coisas: explicar
quais alavancas da operação (logística, atendimento, pedido) movem o NPS; antecipar
quais pedidos tendem a virar detratores usando o que já se sabe durante a jornada; e
ajudar a priorizar onde agir primeiro. Vale reforçar que o objetivo não é caçar a
métrica mais bonita nem o modelo mais complexo, e sim entender o problema e tomar uma
decisão melhor.

## Por que o NPS é importante para um e-commerce?

O NPS resume em uma única pergunta o quanto o cliente confia na marca a ponto de
recomendá-la. Num e-commerce isso pesa muito por alguns motivos.

Primeiro, ele funciona como indicador antecedente de crescimento. Promotor compra de
novo e indica; detrator some e ainda fala mal. Então o NPS costuma sinalizar a receita
futura melhor do que indicadores que só olham o passado.

Segundo, no e-commerce a troca custa quase nada para o cliente, porque o concorrente
está a um clique. Sem barreira de troca, é a experiência que segura o cliente, não a
inércia.

Terceiro, é uma métrica simples e comparável. Dá para comunicar para a liderança em
uma frase e comparar com benchmarks de mercado e com a concorrência. E, por fim, é uma
métrica que conecta o que acontece no dia a dia da operação (um atraso, uma reclamação)
com o resultado de negócio lá na ponta.

## Quais áreas poderiam se beneficiar desses insights?

| Área | Como se beneficia, segundo os dados |
|---|---|
| Logística / Supply Chain | É onde está o maior vilão. O atraso em relação ao prazo prometido é o fator número um, então a área ganha em definir SLA com transportadoras e gerir a promessa de prazo. |
| Atendimento / CX | Reclamação e número de contatos derrubam a nota. O foco vira resolver no primeiro contato e recuperar casos em risco antes que virem detratores. |
| Produto / Operações | Calibrar a expectativa de prazo no checkout (prometer o que dá para cumprir) e tirar fricções que geram reclamação. |
| Pricing / Comercial | Aqui tem um aprendizado: preço, frete e desconto quase não mexem no NPS. Ou seja, desconto não compra satisfação neste cenário, e o investimento rende mais na operação. |
| Liderança / Estratégia | Ajuda a decidir onde colocar dinheiro, definir metas (por exemplo, % de pedidos no prazo) e acompanhar o impacto no NPS. |
| Marketing / CRM | Dá para ativar promotores (indicação, avaliações) e montar jornadas de retenção para quem está em risco. |

## Como o NPS impacta o negócio

Sobre recompra: promotor volta, detrator não. Um detalhe forte da base é que todos os
promotores recompraram em 30 dias, e nenhum detrator recomprou. Como reter custa bem
menos que adquirir um cliente novo, cada detrator que a gente evita protege margem e o
valor do cliente no tempo.

Sobre boca a boca: promotor recomenda de graça, o que barateia a aquisição, enquanto
detrator avisa os outros. No digital isso é amplificado por avaliação pública e redes
sociais, então um detrator consegue afastar vários clientes em potencial.

Sobre market share: recompra e boca a boca se somam. Mais cliente fiel e mais
indicação, a um custo de aquisição menor, vão tomando espaço do concorrente. Num
mercado em que trocar é fácil, NPS sustentado é vantagem competitiva, e um NPS bem
negativo como o atual é basicamente participação de mercado vazando aos poucos.

## Indicadores de mercado que complementariam a análise

Os dados internos explicam o que está acontecendo dentro de casa, mas indicadores
externos dão a referência que falta. Eu olharia para benchmarks de NPS do varejo
online (para saber se -72,8 está muito fora da curva e qual seria uma meta realista),
para o SLA logístico praticado no mercado, comparando prazo prometido com o cumprido e
a taxa de entregas no prazo das transportadoras, e para indicadores de reputação como
Reclame Aqui, tempo de resposta e taxa de solução. Também ajudaria comparar o nosso
NPS com o da concorrência e cruzar tudo isso com indicadores financeiros do cliente
(CAC, LTV, churn e taxa de recompra), que é o que traduz variação de NPS em dinheiro.

Resumindo, o problema é operacional e dá para antecipar. A satisfação é movida por
entrega no prazo e qualidade do atendimento, não por perfil de cliente ou preço, e é
exatamente isso que abre espaço para prever e prevenir a insatisfação, como
desenvolvo nas partes 2, 3 e 4.
