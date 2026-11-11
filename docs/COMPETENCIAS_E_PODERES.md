# Competências e poderes por cargo

O jogo separa o que cada papel pode fazer, com base legal resumida da Constituição de 1988. É um resumo editorial para jogar, não parecer jurídico; confira as fontes antes de citar.

## Estrutura
- `engine/powers_catalog.py`: dados. `ROLES` (eleitor, militante, filiado, dirigente, vereador, prefeito, deputado estadual, governador, deputado federal, senador, presidente) com "pode", "não pode" e base legal; `ACTIONS` (46 ações presidenciais) e `OTHER_OFFICE_ACTIONS` (referência dos demais cargos).
- `engine/powers.py`: regras. Quem pode, qual aprovação, efeitos, custo e mudanças estruturais persistentes (`state["structure"]`).
- `powers_routes.py`: `GET /api/powers`, `GET /api/powers/roles`, `POST /api/powers/execute`.
- Interface: aba Competências (`PowersPanel.jsx`).

## Tipos de aprovação
| Tipo | Regra no jogo |
| --- | --- |
| Decreto | Vale na hora; intervalo de 7 dias da agenda administrativa |
| Medida provisória | Vale na hora; precisa ser convertida em 120 dias, senão a mudança estrutural é revertida; intervalo de 30 dias |
| Projeto de lei / lei complementar / PEC / tratado | Vai à tramitação; votação nominal simulada (Câmara e Senado); PEC com quórum de 3/5 |
| Vedado | Cláusulas pétreas e competências de outros poderes; aparece bloqueado com o motivo |

## Estado do país que as ações mudam
Autonomia do Banco Central (lei complementar → constitucional → subordinado), regras de armas, modelo policial, sistema de governo (com plebiscito simulado), moeda, blocos (BRICS, OPEP+, OTAN, Mercosul), controle de empresas estatais (privatizar/estatizar), reeleição, programa nuclear, Alcântara e obras já feitas.

## Exemplos modelados
Asfaltar ou duplicar rodovia, conceder rodovia e transferir concessão, ferrovia e portos; privatizar ou estatizar empresa; BC (autonomia, meta de inflação, indicação); Alcântara, programa nuclear civil, arma nuclear (só por PEC e saída de tratados, com custo enorme), GLO, intervenção federal, estado de defesa; armas, desmilitarização da polícia (PEC); BRICS, OTAN, OPEP+, Mercosul, acordos comerciais; mudar o sistema de governo (PEC + plebiscito), monarquia e abolição da federação (vedadas); reforma tributária, previdência, teto de gastos, transferência de renda, salário mínimo, desonerações, congelamento de preços.

## Limites desta versão
- Só a Presidência executa ações; os demais cargos mostram o que cabe e as principais iniciativas (descritivas).
- Efeitos são parâmetros de design, aplicados uma vez; não há modelo econômico detalhado.
- Obras e privatizações não têm prazo de entrega nem valor de mercado reais; custos e receitas são fictícios.
- STF, AGU, TSE e polícias ficam para uma etapa futura.
- Uma MP rejeitada reverte as mudanças estruturais, mas não os efeitos já sentidos.
