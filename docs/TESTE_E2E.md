# Teste de ponta a ponta das carreiras

Um jogador automático (`backend/e2e/`) conduz cada carreira pela API, como o navegador faria. Fica **separado** dos testes unitários (`backend/tests/`) porque é mais lento e joga partidas inteiras.

## O que ele faz
Para cada cargo (vereador, prefeito, deputado estadual, governador, deputado federal, senador e presidente), **vencendo e perdendo** a eleição:

1. começa a carreira e confere a pré-campanha;
2. faz uma preparação e, se a espera é longa, usa o pulo para o ano da eleição;
3. faz campanha (comícios) e, perto do dia da eleição, **força o resultado** (vitória ou derrota) para cobrir os dois caminhos;
4. na vitória, toma posse, joga meses de mandato, executa ações do cargo e responde às decisões pendentes;
5. na derrota, confere a oposição e deixa o tempo passar.

Em cada fase ele abre as telas principais (indicadores, histórico, balanço, competências, reguladores, imprensa, CPI, território, Congresso e outras) e confere:
- nenhuma chamada quebra com erro 500;
- a data nunca volta no tempo;
- nenhum indicador fica inválido, e aprovação, governabilidade, base no Congresso, confiança, integridade e credibilidade ficam entre 0 e 100.

Cada partida usa um banco temporário: não mexe no seu banco real.

## Como rodar
```
cd backend
python -m unittest e2e.test_careers -v                      # todos os cargos, 6 meses de mandato (cerca de 2 minutos)
E2E_OFFICES=vereador,presidente python -m unittest e2e.test_careers -v
E2E_MONTHS=48 python -m unittest e2e.test_careers -v        # mandato inteiro (bem mais lento)
```

No GitHub: **Actions > Teste de ponta a ponta (carreiras) > Run workflow**. Também roda toda madrugada. Não bloqueia o deploy da VM; se falhar, aparece como falha na aba Actions.

## Como validar o próprio teste
Provoque um defeito (por exemplo, faça uma rota levantar `RuntimeError` ou ponha `metrics["approval"] = 150`) e rode um cargo: ele deve falhar apontando a rota ou o indicador. Foi assim que o teste foi conferido.

## O que ele não cobre
Interface no navegador (isso é a auditoria `tools/contrast-audit.mjs` e a revisão visual), balanceamento (script de simulação de 48 meses) e o Modo Eleitor.
