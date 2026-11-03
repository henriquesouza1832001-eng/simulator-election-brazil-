# Validação cruzada das propostas de geografia, narrativa e aprendizado

Status: geografia municipal validada, perfil do jogador e perfis políticos fictícios de ministros implementados; a indicação ministerial já altera o apoio dos grupos na próxima campanha presidencial. O log de prévias de interpretação foi iniciado por jogador e correções humanas podem apontar para a prévia correspondente. Classificador local, avaliação de qualidade, personagens persistentes e mandatos locais completos continuam pendentes. Revisado em 3 nov. 2026.

## Estado verificado no repositório

| Área | O que já existe | O que falta |
| --- | --- | --- |
| Geografia | Catálogo versionado dos 5.571 municípios, com código IBGE, nome, UF e estimativa populacional de 2026; `career.py` grava `municipality_id`, expõe o perfil e associa atividades municipais ao local escolhido. | Eleitorado estimado do TSE, perfil econômico, IDHM e temas-âncora ainda não foram importados. Cargos estaduais/federais ainda não fazem visitas cidade a cidade; orçamentos, câmaras e serviços locais também faltam. |
| Personagens | A ficha do jogador fica dentro do save. `appointments.py` cria perfis de candidatos a vagas. | Não há entidade persistente `Character`, ID próprio, histórico de aparições ou ligação a eventos; personagens de nomeações são gerados para aquela etapa. |
| Temas | `issues.py` define IDs e rótulos compartilhados por `career.py` e `campaign.py`; a campanha oferece saúde e educação separadas, preservando `servicos` como alias de saves antigos. | Grupos afetados, termos e rubricas ainda variam por contexto. A geografia ainda não atribui âncoras temáticas porque faltam fontes comparáveis de perfil econômico e IDHM. |
| Espectro e nomeações | A ficha do jogador usa cinco posições e efeitos explícitos por espectro/origem familiar. Candidatos ministeriais fictícios também recebem esses dois campos; nomeá-los desloca em poucos décimos o apoio de grupos na campanha presidencial. | O traço produtivista ainda não foi incluído; seus efeitos precisam ser definidos nos dois modos antes de entrar na ficha. Eixos econômicos, sociais e territoriais do personagem continuam descritivos; não há elenco persistente nem atribuição ideológica aos indicados ao STF. O cálculo de grupos dos dois modos ainda usa catálogos diferentes e precisa de consolidação posterior. |
| Interpretação | Gemini e fallback local classificam medidas; prévias são registradas por jogador em `interpretation_log`, com saída, origem, modelo, versão do prompt e confiança. Correções guardadas em `interpretation_corrections` apontam para a prévia idêntica mais recente do mesmo jogador, quando existe. A tabela `actions` conserva propostas aplicadas. O servidor extrai valores fiscais explícitos do texto e, ao aplicar, recupera a prévia registrada do próprio jogador por ID; valores do navegador e estimativas numéricas da IA não definem o custo. | O log não é conjunto de rótulos: saídas sem correção não treinam o classificador. Ainda faltam avaliação separada e classificador local. A extração fiscal é deliberadamente simples e só reconhece valores monetários explícitos próximos de linguagem de custo; não estima orçamento ausente nem confirma neutralidade fiscal. |
| RAG | `rag.py` ingere e recupera trechos com URL, licença e data; `tse_import.py` guarda proveniência de candidaturas. | `event_evidence_brief()` não tem consumidor no fluxo atual; RAG ainda não fundamenta textos narrativos. O importador TSE não fornece um cadastro de municípios. |
| Saves | `game_campaigns` permite várias partidas nomeadas por jogador; cada save guarda cargo/modo, dificuldade, data e estado, e o histórico de ações usa o mesmo `campaign_id`. Saves antigos migram para `default`. | Exportação e recuperação fora dos snapshots locais ainda faltam; listas e ferramentas de gestão podem crescer depois. |
| Mandatos locais | A carreira reconhece sete cargos e dá ações iniciais por cargo. | Prefeituras e governos estaduais ainda não têm orçamento, serviços, calendário legislativo e câmaras próprios. Votos nominais, bancadas e coalizões também não estão modelados. |

## Decisões de contrato

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

1. **Contrato e compatibilidade, fatia inicial entregue:** centralizar IDs de temas, registrar os campos geográficos e preservar leitura de saves antigos. O servidor já calcula o custo apenas a partir de valores explícitos no texto; qualquer classificador local continua bloqueado até avaliação offline.
2. **Malha municipal, fatia 1 entregue:** importar códigos IBGE, nomes, UF, região e população estimada de 2026 para os 5.571 municípios. `geography.py` documenta faixas de porte e o multiplicador de alcance como mecânica do jogo; ainda não há âncoras temáticas, eleitorado do TSE, IDHM ou perfil econômico.
3. **Localidade na carreira, fatia inicial entregue:** aceitar `municipality_id`, expor dados no resumo, validar município e UF, e anexar localidade às ações municipais. Nomes antigos são resolvidos somente quando correspondem sem ambiguidade; visitas em outros municípios para cargos estaduais/federais seguem pendentes.
4. **Perfis ministeriais, primeira fatia entregue:** candidatos fictícios recebem espectro e origem familiar de forma reproduzível; uma nomeação altera o apoio dos grupos na campanha presidencial. A escala é pequena e não afeta aprovação nacional nem o STF.
5. **Campanhas nomeadas, primeira fatia entregue:** migrar saves antigos para `campaign_id=default`, criar várias partidas nomeadas por conta, validar propriedade no servidor, isolar ações e permitir alternar entre elas. Exportação e recuperação externa continuam pendentes.
6. **Log e validação fiscal, primeira fatia entregue:** registrar prévias por jogador, associar correções à prévia correspondente e recalcular valores fiscais no servidor a partir do texto original. Próximo passo: criar avaliação/treino lexical offline sem ligar o classificador ao fluxo do jogo.
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
