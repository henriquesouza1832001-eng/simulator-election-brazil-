# Reguladores: STF, AGU, tribunais de contas, PF/MP e TSE

Atores que revisam, limitam e investigam o que o jogador faz. Não escolhem políticas. Probabilidades e pesos são parâmetros de design; as bases legais são resumo editorial da Constituição, não parecer jurídico. Código: `engine/regulators.py`, aba Reguladores.

| Regulador | Base | O que faz no jogo |
| --- | --- | --- |
| STF | CF art. 101 a 103-B | Cada decreto, MP ou lei aprovada com risco jurídico acima de 8% abre um processo; o julgamento sai de 45 a 120 dias depois. Se suspender, o regime anterior volta e parte dos efeitos é revertida, com perda de confiança institucional e aprovação. Se mantiver, a confiança sobe um pouco. |
| AGU | CF art. 131 | Mostra, antes de assinar, o parecer de risco (baixo, médio, alto), a chance de suspensão e o fundamento. Não impede o Presidente de assinar. |
| Tribunais de Contas | CF art. 70 a 75 e art. 31 | Uma vez por mês, podem auditar obras em andamento e apontar ressalvas (a confiança do cargo cai um pouco). |
| PF, CGU e MP | CF art. 127 a 130-A; art. 144, §1º | Quando a integridade cai abaixo de 60, cresce a chance mensal de inquérito, com perda de integridade e aprovação. |
| TSE | CF art. 118 a 121; LC 64/1990 e 135/2010; Lei 9.504/1997 | Mostra o histórico de conduta da campanha (já calculado pelo motor de carreira): condutas tentadas, detectadas e a penalidade de votos. |

## Risco jurídico
Cada ação presidencial tem um risco-base (`RISK`), como 0,70 para congelamento de preços por MP e 0,90 para arma nuclear; os demais usam o padrão do instrumento. O STF fica mais favorável ao governo com ministros indicados e confirmados pelo Senado (até 50% de redução do risco efetivo). Os julgamentos são determinísticos por partida (semente).

## Limites
- Só atos presidenciais passam pelo STF; ações de cargos locais e legislativos ainda não geram processos.
- O STF não tem ministros individuais com votos; o alinhamento é um número agregado.
- Tribunais de contas e PF/MP agem por probabilidade mensal, sem processo de defesa.
- Registro e impugnação de candidaturas (Ficha Limpa) pelo TSE ainda não são simulados.
- TCU, AGU e PF não têm ações próprias que o jogador possa acionar; é o próximo passo.
