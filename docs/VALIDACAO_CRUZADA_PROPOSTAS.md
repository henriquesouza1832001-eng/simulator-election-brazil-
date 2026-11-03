# Validação cruzada das propostas de geografia, narrativa e aprendizado

Status: geografia municipal validada, perfil do jogador e perfis políticos fictícios de ministros implementados; a indicação ministerial já altera o apoio dos grupos na próxima campanha presidencial. Prévia e correção estruturada são isoladas por jogador; o classificador de categoria/instrumento pode ser avaliado offline e produzir artefato candidato, ainda sem uso em partidas. Personagens persistentes e mandatos locais completos continuam pendentes. Revisado em 3 nov. 2026.

## Estado verificado no repositório

| Área | O que já existe | O que falta |
| --- | --- | --- |
| Geografia | Catálogo versionado dos 5.571 municípios, com código IBGE, população estimada de 2026 e eleitorado apto do TSE 2026; a carreira valida o município de candidatura e visitas municipais para cargos estaduais/federais, registra apoio por cidade e pondera o efeito na UF ou no país pela participação do eleitorado local. A campanha presidencial também pondera a projeção regional pelo eleitorado da cidade. | Perfil econômico, IDHM e temas-âncora ainda não foram importados. Orçamentos, câmaras e serviços locais também faltam. |
| Personagens | A ficha do jogador fica dentro do save. `appointments.py` cria perfis de candidatos a vagas. | Não há entidade persistente `Character`, ID próprio, histórico de aparições ou ligação a eventos; personagens de nomeações são gerados para aquela etapa. |
| Temas | `issues.py` define IDs e rótulos compartilhados por `career.py` e `campaign.py`; a campanha oferece saúde e educação separadas, preservando `servicos` como alias de saves antigos. | Grupos afetados, termos e rubricas ainda variam por contexto. A geografia ainda não atribui âncoras temáticas porque faltam fontes comparáveis de perfil econômico e IDHM. |
| Espectro e nomeações | A ficha do jogador usa cinco posições e efeitos explícitos por espectro/origem familiar. Candidatos ministeriais fictícios também recebem esses dois campos; nomeá-los desloca em poucos décimos o apoio de grupos na campanha presidencial. | O traço produtivista ainda não foi incluído; seus efeitos precisam ser definidos nos dois modos antes de entrar na ficha. Eixos econômicos, sociais e territoriais do personagem continuam descritivos; não há elenco persistente nem atribuição ideológica aos indicados ao STF. O cálculo de grupos dos dois modos ainda usa catálogos diferentes e precisa de consolidação posterior. |
| Interpretação | Gemini e fallback local classificam medidas; prévias são registradas por jogador em `interpretation_log`, com saída, origem, modelo, versão do prompt e confiança. A tela salva correções de categoria e instrumento em `interpretation_corrections`, ligadas à última prévia idêntica do mesmo jogador, se existir. O treinador agrupa exemplos por jogador, deduplica textos repetidos e mantém a correção mais recente por campo. `python -m app.ai.trainer` avalia um Naive Bayes lexical em holdout e grava candidato somente com duas classes qualificadas e pelo menos 75% de acurácia; não integra esse artefato ao fluxo ativo. A tabela `actions` conserva propostas aplicadas. O servidor extrai valores fiscais explícitos do texto e, ao aplicar, recupera a prévia registrada do próprio jogador por ID; valores do navegador e estimativas numéricas da IA não definem o custo. | Ainda faltam um conjunto maior e diversificado, avaliação contínua em dados novos e decisão explícita de ativação do classificador. O candidato prevê somente categoria ou instrumento; não estima custo, legalidade nem efeito. A extração fiscal é deliberadamente simples e só reconhece valores monetários explícitos próximos de linguagem de custo; não estima orçamento ausente nem confirma neutralidade fiscal. |
| RAG | `rag.py` ingere e recupera trechos com URL, licença e data; `tse_import.py` guarda proveniência de candidaturas. | `event_evidence_brief()` não tem consumidor no fluxo atual; RAG ainda não fundamenta textos narrativos. O importador TSE não fornece um cadastro de municípios. |
| Saves | `game_campaigns` permite várias partidas nomeadas por jogador; cada save guarda cargo/modo, dificuldade, data e estado, e o histórico de ações usa o mesmo `campaign_id`. Saves antigos migram para `default`. | Exportação e recuperação fora dos snapshots locais ainda faltam; listas e ferramentas de gestão podem crescer depois. |
| Mandatos locais | A carreira reconhece sete cargos e dá ações iniciais por cargo. | Prefeituras e governos estaduais ainda não têm orçamento, serviços, calendário legislativo e câmaras próprios. Votos nominais, bancadas e coalizões também não estão modelados. |

## Decisões de contrato

### Dados públicos, personagens reais e sátira

O catálogo público pode identificar candidaturas e partidos com fonte, ano,
data de consulta e licença. A narrativa inventada deve usar personagens
fictícios; não atribuir falas, crimes ou escândalos simulados a pessoas reais.
Fotos e caricaturas exigem proveniência e direitos verificados por arquivo.
O aviso de sátira não substitui essas verificações. O contrato completo e as
fontes oficiais ficam em [`DADOS_PUBLICOS_E_SATIRA.md`](DADOS_PUBLICOS_E_SATIRA.md).

### 1. Cidade, personagem e local da ação são campos diferentes

- `municipality_id` será o código IBGE de sete dígitos, armazenado como texto para preservar o formato e servir de chave estável.
- `Character.birth_municipality_id` será opcional. Jornalistas nacionais, figuras institucionais e personagens sem vínculo local podem não ter cidade de origem.
- A candidatura terá sua própria `municipality_id` quando o cargo for municipal; atividades e eventos guardarão o município onde ocorreram. Origem do personagem não será usada como local automático da atividade.
- Saves antigos manterão o nome livre como campo legado. A migração só associará um código quando a correspondência for inequívoca; nomes ambíguos ficam sem vínculo até escolha explícita.
- O catálogo inicial já contém todos os municípios e a população estimada de 2026, com origem e data de referência registradas. Porte e alcance de campanha são parâmetros fictícios documentados; ampliar fontes municipais e temas-âncora virá depois.

### 2. Temas compartilham IDs; saliência e ideologia não compartilham escala

- Criar um catálogo canônico de temas, por exemplo `economia`, `trabalho`, `saude`, `educacao`, `seguranca`, `mobilidade` e `integridade`.
- `campaign.py`, `career.py`, eventos e temas-âncora usarão esses IDs. Grupos afetados e termos de discurso continuam configuráveis por contexto, mas não redefinem o ID do tema.
- O tema antigo `servicos`, usado pela campanha presidencial, será tratado como alias legado que cobre saúde e educação. Saves e ações antigas continuam legíveis; novas ações registram o tema canônico.
- A saliência municipal será um peso determinístico por tema, em escala documentada de 0 a 1. O vetor ideológico usará eixos próprios, em escala de −1 a +1, e tags não exclusivas. Pontos ideais dos grupos usarão a escala ideológica. Não somar nem comparar esses valores diretamente.

### 3. Personagem persistente com contexto geográfico opcional

`Character` terá ID estável dentro da partida, nome, papéis e histórico, traços, vetor ideológico e `birth_municipality_id` opcional. Eventos referenciam `character_id` e `municipality_id` separadamente. A geração permanece reproduzível pela semente e os dados inventados recebem o selo de simulação.

### 3a. Origem e território eleitoral são independentes

- `birth_state_code` e `birth_municipality_id` são opcionais e validados juntos contra o catálogo municipal do IBGE.
- `state_code` e `municipality_id` da candidatura descrevem o território eleitoral, nunca preenchem a origem do personagem por inferência.
- Vereador e prefeito exigem cidade eleitoral válida; cargos estaduais e federais aceitam UF sem município; presidente usa “Brasil” como território da campanha e não pede município eleitoral.
- Cidades digitadas fora do catálogo não são aceitas. Cidades opcionais só são enviadas se o jogador escolheu uma sugestão válida.

### 4. Aprendizado de interpretação separado da avaliação narrativa

- `interpretation_log` começa restrito à tarefa `policy_interpretation`: texto, saída, origem/modelo/versão do prompt, confiança, data e referência a eventual correção humana.
- Saídas do Gemini são previsões, não rótulos corretos. O treino supervisionado usa correções confirmadas pelo jogador; saídas sem revisão servem para auditoria e análise, não como verdade automática.
- Avaliação de narrativa terá tabela/tarefa própria, ligada a `event_id` e `character_id`, com critérios próprios. Não misturar esse conjunto com categorias de medidas.
- Primeiro treinar e avaliar offline com conjunto separado. Só depois permitir que o modelo local seja primeira tentativa por categoria; Gemini e fallback seguem como alternativas enquanto a qualidade não passar o limite definido.

### 5. Fronteira canônica entre IA e motor

O motor Python é a autoridade para validar ações, alterar o estado e calcular custos, probabilidades, efeitos e resultados. A IA pode classificar intenção, sugerir rótulos e redigir explicações a partir do contexto permitido. Números escritos pelo jogador podem ser extraídos como entradas, mas precisam ser validados no servidor contra a proposta original; um número produzido ou alterado pelo modelo não pode se tornar custo ou efeito por si só.

**Regra implementada:** `fiscal_cost_bi` é recalculado no servidor a partir do texto original, usando apenas valores monetários explícitos próximos de termos fiscais. A rota de aplicação recebe o ID da prévia, verifica se ela pertence ao jogador autenticado e se o texto coincide; depois recalcula o custo antes de chamar `forecast()` ou `apply_effects()`. Se o texto não informar valor, a prévia mostra R$ 0 usado no cálculo e avisa que isso não prova neutralidade fiscal. A extração ainda não substitui uma estimativa orçamentária completa. Não ativar treinamento local sem avaliação separada e conjunto revisado.

### 6. Várias campanhas por conta

**Primeira fatia implementada:** `game_campaigns` guarda várias partidas por `player_id`, com ID, nome, cargo/modo, dificuldade, data e estado. A interface lista e abre uma partida; uma partida nova recebe ID separado e não substitui as outras. O servidor valida a propriedade do ID recebido no cabeçalho antes de ler o save, e o histórico de ações usa também `campaign_id`. O save antigo é migrado para `default`; exportação e transferência autônoma continuam pendentes. A restauração operacional via S3 está definida na stack AWS, aguardando um ciclo real.

## Sequência de implementação recomendada

1. **Contrato e compatibilidade, fatia inicial entregue:** centralizar IDs de temas, registrar os campos geográficos e preservar leitura de saves antigos. O servidor já calcula o custo apenas a partir de valores explícitos no texto; classificador local segue bloqueado no fluxo ao vivo até avaliação em dados novos.
2. **Malha municipal, fatias 1 a 3 entregues:** importar codigos IBGE, nomes, UF, regiao e populacao estimada de 2026 para os 5.571 municipios; agregar eleitorado apto do TSE 2026; e exibir PIB e PIB por pessoa de 2023 mais composicao setorial de 2021 quando comparavel. `geography.py` expoe as participacoes eleitorais e o perfil economico descritivo. As faixas de alcance continuam sendo mecanicas do jogo; IDHM e ancoras tematicas seguem pendentes. Detalhes e limites economicos em [`PERFIL_ECONOMICO_MUNICIPAL.md`](PERFIL_ECONOMICO_MUNICIPAL.md).
3. **Localidade na carreira, fatias iniciais entregues:** aceitar `municipality_id`, validar município e UF e anexar localidade às ações municipais, estaduais e federais. A ação guarda apoio local; visitas para disputas maiores ponderam o efeito territorial pelo eleitorado do município dentro da UF, enquanto a disputa presidencial usa a participação no eleitorado nacional. Nomes antigos só são resolvidos quando a correspondência é inequívoca.
4. **Perfis ministeriais, primeira fatia entregue:** candidatos fictícios recebem espectro e origem familiar de forma reproduzível; uma nomeação altera o apoio dos grupos na campanha presidencial. A escala é pequena e não afeta aprovação nacional nem o STF.
5. **Campanhas nomeadas, primeira fatia entregue:** migrar saves antigos para `campaign_id=default`, criar várias partidas nomeadas por conta, validar propriedade no servidor, isolar ações e permitir alternar entre elas. Exportação e recuperação externa continuam pendentes.
6. **Log, correção e treino offline, primeira fatia entregue:** registrar prévias por jogador, aceitar rótulos revisados de categoria/instrumento, associar a correção à prévia correspondente, e avaliar candidatos lexicais por jogador sem ativá-los. O servidor continua recalculando valores fiscais no texto original. Próximo passo: coletar exemplos variados, avaliar em dados posteriores e só então decidir se algum classificador pode sugerir rótulos no fluxo do jogo.
7. **Personagens persistentes e espectro:** criar IDs, papéis, histórico, origem opcional e vetores ideológicos; ligar personagens a eventos e disputas após os contratos anteriores estarem estáveis.
8. **Pontuação municipal e narrativa:** usar saliência municipal na pertinência do discurso e nos efeitos locais. Integrar RAG à narrativa apenas depois de definir a avaliação narrativa separada e exibição de fontes/limites.
9. **Mandatos subnacionais e Legislativo:** criar orçamento/serviços/câmaras por ente; depois ligar partidos, bancadas, comissões, coalizões e votos nominais. Não inferir voto legislativo apenas do rótulo ideológico.

Cada fatia termina com regra determinística, estado persistido, endpoint, interface focada e atualização dos documentos. Testes unitários e avaliações sintéticas são critérios de aceite para essas fatias.

## Uso de referências públicas

Siglas e nomes de partidos podem vir do catálogo público do TSE, com URL e data de consulta. O catálogo não presume linha ideológica: a linha escolhida na partida é um parâmetro ficcional. Nomes públicos, cargos e dados eleitorais só entram com fonte e data; notícias, falas, pesquisas, alianças e eventos satíricos recebem rótulo de ficção. O aviso de sátira não substitui busca de marca, atribuição de imagens ou revisão de direitos antes de divulgação comercial. Nome de trabalho atual: Civiciclo; a disponibilidade no INPI ainda não foi confirmada.

## Critérios de aceite das três propostas

- Duas cidades com dados e temas diferentes produzem prévias de campanha explicáveis e reproduzíveis pela mesma semente.
- Um personagem reaparece com o mesmo ID e histórico, e uma atividade não é atribuída automaticamente à cidade de origem dele.
- Mudanças no vetor ideológico afetam somente afinidades documentadas; saliência de cidade nunca é confundida com posição ideológica.
- Uma interpretação não aprovada pelo jogador não entra como rótulo de treino. Dados de avaliação narrativa não alteram o classificador de medidas.
- Um save antigo abre sem perder a candidatura textual; mais de uma campanha pode ser criada e recuperada sob a mesma conta, sem cruzar proprietários.
- Resumos e listas permanecem curtos; contexto municipal, personagem, proveniência e rubrica detalhada abrem sob demanda.
