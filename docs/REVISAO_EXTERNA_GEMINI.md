# Revisão externa (Gemini) — o que adotar

Origem: o zip do projeto foi enviado ao Gemini como revisor externo (19 nov. 2026). Abaixo, o que ele disse conferido contra o código. Todos os arquivos que ele citou existem; algumas ideias dele já estão prontas e outras dependem de decisões suas.

## Concordo e é prioridade
| Achado | Conferência | Ação |
|---|---|---|
| "Caixa-preta": o jogador não sabe por que um número mudou | Não há "principais causas" no retorno da API. Só há `drivers` estáticos em `answer_context.py` | **Por que mudou?**: o motor devolve as 3 maiores causas da variação de aprovação, caixa e intenção de voto; a tela mostra em dica ou resumo |
| Excesso de abas, sem filtro do que é urgente | Hoje há metas da fase na Agenda (feito em 19/11), mas não uma pasta única de pendências | **Mesa de despacho**: 3 a 5 pendências da semana no Painel (decisão, sanção, crise, convocação) |
| Arquivos grandes: `career.py` 139 KB (2.006 linhas), `App.jsx` 71 KB, `CareerPanel.jsx` 69 KB, `main.py` 67 KB | Confirmado | Dividir `career.py` em módulos (campanha, governo, eleição, metas) **com os testes atuais como rede**, uma fatia por vez |
| Tom satírico se perde em texto burocrático | Concordo: manchetes e eventos soam como relatório | Passada de texto nos eventos e na Imprensa; manchetes com humor (ver abaixo) |
| Cenário curto de entrada | Não existe; `historical_play.py` é o modo de comparar com a eleição real do TSE, não um tutorial | **"100 dias"**: prefeito herda cidade em crise, 15 minutos, um clique no início |

## Já existe (o Gemini não viu ou o zip não deixou claro)
- **Feedback da leitura do discurso**: pronto em 19/11 (`SpeechReading.jsx`, mostra temas, tom, promessas com meta, prazo e recurso, ataques e riscos).
- **Memória de promessas de campanha**: existe (`campaign_promises` em `career.py`, conferidas após 1 ano no cargo).
- **Veto, derrubada e sanção tácita**: existe em `congress_agenda.py`. Falta só o drama de sessão.
- **Medida provisória que tranca a pauta**: existe (45 dias, mais 60 e 60) com `test_mp_pauta.py`.
- **Faixa de mercado reagindo às canetadas**: existe (`MercadoFaixa`, `macro.py`).
- **Crises sazonais por lugar**: existem em `crises_local.py`.

## Depende de decisão sua
- **Manchetes por linha editorial (governista, oposição, redes)** usam o recurso `narrar` do Gemini, que está **desligado por decisão** (`GEMINI_RECURSOS=interpretar,mapear`). Dá para fazer com textos do motor primeiro e ligar o Gemini depois; o custo por mandato ainda não foi medido.
- **Plataforma-alvo (web, Steam ou celular)**, **sessão curta ou longa** e **limite da sátira com cidades reais**: perguntas dele que mudam o desenho da interface. Respondê-las evita retrabalho.
- **Monetização e Workshop**: só depois da 1.0.

## Ideias boas para depois (esforço médio)
Dossiê contra rival no debate; teto de rejeição separado do voto fiel; palanque regional; balcão de emendas visual; fogo amigo de ministro ambicioso; pedalada fiscal com bomba-relógio; greves setoriais; CPI em fases; boatos virais; cenários históricos temáticos; modo "sobrevivência"; página fictícia do legado ao fim do mandato; desafio semanal com seed fixa.

## Descartar ou adiar
- Cronômetro em entrevistas: irrita em jogo de leitura; adiar.
- Cabo eleitoral com percentual fixo por cidade: o motor já usa força real do TSE por partido; entraria melhor como parte de coalizões.

## Ordem sugerida (substitui o resto do passo 3 por enquanto)
1. **Por que mudou?** (causas da variação) — menor custo, maior efeito em "nada faz sentido".
2. **Mesa de despacho** no Painel.
3. **Cenário "100 dias"** como botão principal na tela inicial.
4. **Passada de tom** nos textos + manchetes do motor (Gemini depois).
5. **Dividir `career.py`** em módulos, uma fatia por vez, sempre com a suíte verde.
6. Retomar o motor eleitoral (coalizões, TV, debate) em cima disso.

## Andamento
- **Item 1 feito (19/11/2026):** "Por que mudou?" no Painel (`engine/drivers.py`): as 3 maiores causas da variação de aprovação, inflação, PIB, desemprego, base no Congresso e confiança institucional; inflação, PIB e desemprego decompostos por termo do motor macro. Testes em `test_por_que_mudou.py`.
- **Segundo envio ao Gemini:** pacote com capturas de tela, textos reais das telas, inventário do código, autoavaliação em 12 dimensões e meta 9,5 em cada uma.
