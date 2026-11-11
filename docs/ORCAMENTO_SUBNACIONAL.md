# Orcamento subnacional no simulador

Prefeitos e governadores recebem uma reserva anual simulada para programas de governo. Ela nao representa a LOA, a receita oficial ou o limite de gasto do ente. O jogo usa uma regra simples e auditavel ate que receitas, transferencias e execucao por programa sejam modeladas.

## Regra de escala

- Prefeitura: reserva de referencia de R$ 350 milhoes para 100 mil habitantes.
- Governo estadual: reserva de referencia de R$ 12 bilhoes para 5 milhoes de habitantes.
- A populacao municipal vem da estimativa IBGE 2026. A estadual e a soma das estimativas municipais da mesma UF.
- O valor anual e a escala dos custos dos programas variam na mesma proporcao da populacao. Assim, uma acao de referencia compromete uma parcela parecida da reserva em territorios de tamanhos diferentes.
- O custo e multiplicado pelo indice de precos do mandato. No fechamento de cada ano, o motor aplica a inflacao simulada do periodo, limitada a variacao de 0% a 25%, ao indice e recalcula a reserva para o novo ano.
- A reserva anual e renovada no inicio do ano; saldo nao usado nao acumula. Compromissos em andamento continuam no historico e nos relatorios.

Os custos-base por area e os valores de referencia ficam em `career.py`. Indicadores de resultado e efeitos continuam deterministas. A origem, a escala populacional, o ano de referencia e o indice de precos ficam registrados na previa e na acao executada.

## Compatibilidade e limites

Saves antigos preservam a fracao da reserva que ainda estava disponivel quando a nova regra e aplicada. Novas posses ja iniciam com a escala territorial correta. O perfil economico municipal nao altera custos nem apoio eleitoral.

Esta regra nao inclui transferencias federativas, receita propria, folha, divida, empenho, contratos, camara municipal ou assembleia estadual. Esses sao passos seguintes da simulacao fiscal local.

## Fonte demografica

- [IBGE SIDRA, estimativa municipal de populacao 2026](https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/2026/variaveis/9324?localidades=N6%5Ball%5D)
- [Catalogo municipal e proveniencia](ATRIBUICAO_E_FONTES.md)

## Contas locais e LRF (10 nov. 2026)

`engine/subnational_fiscal.py` acrescenta ao prefeito e ao governador:
- **RCL do modelo** = reserva anual x 8 (parâmetro de design).
- **Despesa com pessoal** (limites da LRF art. 20: 54% da RCL no Executivo municipal, 49% no estadual; alerta a 90% e limite prudencial a 95%, art. 22 e 59) e **dívida** (Resolução 40/2001 do Senado: 1,2 RCL município, 2,0 RCL estado). Valores iniciais são parâmetros do jogo.
- Acima do limite prudencial, o jogo bloqueia reajuste e concurso; acima do limite, a confiança cai todo mês até a recondução (art. 23). Operação de crédito aumenta a reserva e a dívida e é bloqueada no limite.
- **Obras do território** deixam de usar a dívida nacional: a parcela anual sai da reserva do cargo e se repete a cada ano até a entrega.
- **Resumo mensal** (executado, folha, dívida, situação) em `/api/fiscal/local` e na aba Competências.

Ainda não há receita própria detalhada, transferências (FPM, FPE, ICMS), empenho por programa nem Câmara/Assembleia aprovando o orçamento.
