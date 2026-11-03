# Validação cruzada das propostas de geografia, narrativa e aprendizado

Status: primeira fatia de geografia e temas canônicos implementada e verificável localmente; personagens, autoaprendizado e mandatos locais completos continuam pendentes. Esta revisão compara as propostas com o código existente e organiza a sequência de trabalho. Não requer deploy.

## Estado verificado no repositório

| Área | O que já existe | O que falta |
| --- | --- | --- |
| Geografia | Catálogo versionado dos 5.571 municípios, com código IBGE, nome, UF e estimativa populacional de 2026; `career.py` grava `municipality_id`, expõe o perfil e associa atividades municipais ao local escolhido. | Eleitorado estimado do TSE, perfil econômico, IDHM e temas-âncora ainda não foram importados. Cargos estaduais/federais ainda não fazem visitas cidade a cidade; orçamentos, câmaras e serviços locais também faltam. |
| Personagens | A ficha do jogador fica dentro do save. `appointments.py` cria perfis de candidatos a vagas. | Não há entidade persistente `Character`, ID próprio, histórico de aparições ou ligação a eventos; personagens de nomeações são gerados para aquela etapa. |
| Temas | `issues.py` define IDs e rótulos compartilhados por `career.py` e `campaign.py`; a campanha oferece saúde e educação separadas, preservando `servicos` como alias de saves antigos. | Grupos afetados, termos e rubricas ainda variam por contexto. A geografia ainda não atribui âncoras temáticas porque faltam fontes comparáveis de perfil econômico e IDHM. |
| Espectro | A ficha do jogador tem um rótulo de espectro e há efeitos iniciais por espectro/família. | Não há vetor ideológico multidimensional aplicado a personagens, grupos e nomeações. |
| Interpretação | Gemini e fallback local classificam medidas; correções do jogador são guardadas por jogador e recuperadas lexicalmente. A tabela `actions` conserva propostas aplicadas. | Não há log de todas as prévias, conjunto de avaliação separado nem classificador local de texto. A saída Gemini inclui `fiscal_cost_bi`, que hoje é usada na previsão e na aplicação; portanto, o limite entre interpretação e cálculo ainda não está integralmente garantido. |
| RAG | `rag.py` ingere e recupera trechos com URL, licença e data; `tse_import.py` guarda proveniência de candidaturas. | `event_evidence_brief()` não tem consumidor no fluxo atual; RAG ainda não fundamenta textos narrativos. O importador TSE não fornece um cadastro de municípios. |
| Saves | Cada jogador tem uma partida ativa e até 12 arquivos recuperáveis. | `game_saves` tem uma linha por jogador; arquivos são snapshots, não várias campanhas ativas nomeadas. |
| Mandatos locais | A carreira reconhece sete cargos e dá ações iniciais por cargo. | Prefeituras e governos estaduais ainda não têm orçamento, serviços, calendário legislativo e câmaras próprios. Votos nominais, bancadas e coalizões também não estão modelados. |

## Decisões de contrato

### 1. Cidade, personagem e local da ação são campos diferentes

- `municipality_id` será o código IBGE de sete dígitos, armazenado como texto para preservar o formato e servir de chave estável.
- `Character.home_municipality_id` será opcional. Jornalistas nacionais, figuras institucionais e personagens sem vínculo local podem não ter cidade de origem.
- A candidatura terá sua própria `municipality_id` quando o cargo for municipal; atividades e eventos guardarão o município onde ocorreram. Origem do personagem não será usada como local automático da atividade.
- Saves antigos manterão o nome livre como campo legado. A migração só associará um código quando a correspondência for inequívoca; nomes ambíguos ficam sem vínculo até escolha explícita.
- O catálogo inicial já contém todos os municípios e a população estimada de 2026, com origem e data de referência registradas. Porte e alcance de campanha são parâmetros fictícios documentados; ampliar fontes municipais e temas-âncora virá depois.

### 2. Temas compartilham IDs; saliência e ideologia não compartilham escala

- Criar um catálogo canônico de temas, por exemplo `economia`, `trabalho`, `saude`, `educacao`, `seguranca`, `mobilidade` e `integridade`.
- `campaign.py`, `career.py`, eventos e temas-âncora usarão esses IDs. Grupos afetados e termos de discurso continuam configuráveis por contexto, mas não redefinem o ID do tema.
- O tema antigo `servicos`, usado pela campanha presidencial, será tratado como alias legado que cobre saúde e educação. Saves e ações antigas continuam legíveis; novas ações registram o tema canônico.
- A saliência municipal será um peso determinístico por tema, em escala documentada de 0 a 1. O vetor ideológico usará eixos próprios, em escala de −1 a +1, e tags não exclusivas. Pontos ideais dos grupos usarão a escala ideológica. Não somar nem comparar esses valores diretamente.

### 3. Personagem persistente com contexto geográfico opcional

`Character` terá ID estável dentro da partida, nome, papéis e histórico, traços, vetor ideológico e `home_municipality_id` opcional. Eventos referenciam `character_id` e `municipality_id` separadamente. A geração permanece reproduzível pela semente e os dados inventados recebem o selo de simulação.

### 4. Aprendizado de interpretação separado da avaliação narrativa

- `interpretation_log` começa restrito à tarefa `policy_interpretation`: texto, saída, origem/modelo/versão do prompt, confiança, data e referência a eventual correção humana.
- Saídas do Gemini são previsões, não rótulos corretos. O treino supervisionado usa correções confirmadas pelo jogador; saídas sem revisão servem para auditoria e análise, não como verdade automática.
- Avaliação de narrativa terá tabela/tarefa própria, ligada a `event_id` e `character_id`, com critérios próprios. Não misturar esse conjunto com categorias de medidas.
- Primeiro treinar e avaliar offline com conjunto separado. Só depois permitir que o modelo local seja primeira tentativa por categoria; Gemini e fallback seguem como alternativas enquanto a qualidade não passar o limite definido.

### 5. Fronteira canônica entre IA e motor

O motor Python é a autoridade para validar ações, alterar o estado e calcular custos, probabilidades, efeitos e resultados. A IA pode classificar intenção, sugerir rótulos e redigir explicações a partir do contexto permitido. Números escritos pelo jogador podem ser extraídos como entradas, mas precisam ser validados no servidor contra a proposta original; um número produzido ou alterado pelo modelo não pode se tornar custo ou efeito por si só.

**Pendência antes do autoaprendizado:** atualmente `fiscal_cost_bi` vem da interpretação enviada pelo navegador e afeta `forecast()` e `apply_effects()`. Ajustar essa entrada para validá-la no servidor (ou exigir confirmação estruturada do jogador) antes de registrar exemplos de treino. Consolidar a regra em `docs/SISTEMAS_E_REGRAS.md`; README e documentos de produto devem apontar para ela.

### 6. Várias campanhas por conta

O requisito continua aberto: `game_saves.player_id` é único e `game_archives` guarda somente snapshots recuperáveis. A próxima estrutura deve dar a cada campanha um `campaign_id` próprio, nome, cargo, dificuldade, fase, data de atualização e estado, sempre associada ao `player_id` autenticado. Cada rota deve validar a propriedade da campanha; o navegador não escolhe o dono pelo corpo da requisição.

## Sequência de implementação recomendada

1. **Contrato e compatibilidade, fatia inicial entregue:** centralizar IDs de temas, registrar os campos geográficos e preservar leitura de saves antigos. A validação do custo fiscal fornecido pela interpretação continua pendente antes de treinar qualquer classificador.
2. **Malha municipal, fatia 1 entregue:** importar códigos IBGE, nomes, UF, região e população estimada de 2026 para os 5.571 municípios. `geography.py` documenta faixas de porte e o multiplicador de alcance como mecânica do jogo; ainda não há âncoras temáticas, eleitorado do TSE, IDHM ou perfil econômico.
3. **Campanhas nomeadas:** migrar de uma linha ativa por jogador para partidas identificadas por `campaign_id`, preservando o save e arquivos atuais. Esse passo permite testar percursos em paralelo sem perder a partida.
4. **Localidade na carreira, fatia inicial entregue:** aceitar `municipality_id`, expor dados no resumo, validar município e UF, e anexar localidade às ações municipais. Nomes antigos são resolvidos somente quando correspondem sem ambiguidade; visitas em outros municípios para cargos estaduais/federais seguem pendentes.
5. **Log e avaliador de interpretação:** registrar todas as prévias de medidas e correções confirmadas. Criar o treino lexical offline sem ligá-lo ao fluxo de jogo.
6. **Personagens persistentes e espectro:** criar IDs, papéis, histórico, origem opcional e vetores ideológicos; ligar personagens a eventos e disputas após os contratos anteriores estarem estáveis.
7. **Pontuação municipal e narrativa:** usar saliência municipal na pertinência do discurso e nos efeitos locais. Integrar RAG à narrativa apenas depois de definir a avaliação narrativa separada e exibição de fontes/limites.
8. **Mandatos subnacionais e Legislativo:** criar orçamento/serviços/câmaras por ente; depois ligar partidos, bancadas, comissões, coalizões e votos nominais. Não inferir voto legislativo apenas do rótulo ideológico.

Cada fatia termina com regra determinística, estado persistido, endpoint, interface focada e atualização dos documentos. Testes unitários e avaliações sintéticas são critérios de aceite para essas fatias; este documento não executa nem substitui esses testes.

## Critérios de aceite das três propostas

- Duas cidades com dados e temas diferentes produzem prévias de campanha explicáveis e reproduzíveis pela mesma semente.
- Um personagem reaparece com o mesmo ID e histórico, e uma atividade não é atribuída automaticamente à cidade de origem dele.
- Mudanças no vetor ideológico afetam somente afinidades documentadas; saliência de cidade nunca é confundida com posição ideológica.
- Uma interpretação não aprovada pelo jogador não entra como rótulo de treino. Dados de avaliação narrativa não alteram o classificador de medidas.
- Um save antigo abre sem perder a candidatura textual; mais de uma campanha pode ser criada e recuperada sob a mesma conta, sem cruzar proprietários.
- Resumos e listas permanecem curtos; contexto municipal, personagem, proveniência e rubrica detalhada abrem sob demanda.
