# Modelo de dados do PLANALTO (esquema observado)

Fonte: corpo da chamada `POST /api/partida` (autosave) lido passivamente na sessão do usuário via REA `inspect_web_page` (formas de corpo; **só nomes e tipos, nenhum valor**). 9 nov. 2026. 23.976 nós, profundidade 7, 2.209 campos.

**Leitura:** o estado completo da partida é um único objeto JSON (`estado`) enviado ao servidor — o motor do jogo roda no cliente e o servidor guarda o save e faz a IA (`/api/ia/*`). Isto é uma inferência a partir do formato da chamada.

## Chaves de primeiro nível de `estado` (81)

`abin`, `acordos`, `ambiente`, `ano`, `apoioEmpresarial`, `aprovacao`, `aprovacaoHistorico`, `base`, `caixa`, `campanha2026`, `capitalPolitico`, `chamadasIa`, `clima`, `coalizao`, `combustivel`, `compromissos`, `compromissosDeCampanha`, `conquistas`, `conquistasNovas`, `consequencias`, `cpis`, `criadoEm`, `crise`, `crisesArmadas`, `custoIa`, `deputados`, `economia`, `embalo`, `empresas`, `escandalos`, `especiais`, `estados`, `eventoAtual`, `eventosVistos`, `exposicao`, `faccoes`, `fase`, `favores`, `federacoes`, `filiacoes`, `fim`, `gabinete`, `gastoCongresso`, `grupos`, `historicoEconomia`, `influencia`, `isolamento`, `manchetes`, `mandato`, `mandatosSeguidos`, `mecanicas`, `melhorSequencia`, `memoriaCrises`, `mes`, `metas`, `militares`, `ministros`, `oposicao`, `organizacoes`, `pais`, `paises`, `partidos`, `personagens`, `pessoal`, `posts`, `presidente`, `pressaoImpeachment`, `projetos`, `redes`, `regime`, `registro`, `repressao`, `resistencia`, `ruas`, `senadores`, `sequencia`, `supremo`, `turno`, `versao`, `vice`, `visitas`



## Deputado/senador (mesma forma, campo `casa`) — `estado.deputados.[]`

`bancadas.[]`:string, `eixos.ambiental`:number, `eixos.autoridade`:number, `eixos.economico`:number, `eixos.federalismo`:number, `eixos.social`:number



## Grupo social — `estado.grupos.[]`

`eixos.ambiental`:number, `eixos.autoridade`:number, `eixos.economico`:number, `eixos.federalismo`:number, `eixos.social`:number, `sensibilidade.crescimento`:number, `sensibilidade.desemprego`:number, `sensibilidade.inflacao`:number, `sensibilidade.juros`:number, `sensibilidade.seguranca`:number



## Estado — `estado.estados.[]`





## Economia — `estado.economia`

`arrecadacao`:number, `bolsa`:number, `cambio`:number, `commodities`:number, `confiancaEmpresarial`:number, `credibilidade`:number, `crescimento`:number, `custoSeguradoAntes`:number, `desemprego`:number, `dividaPib`:number, `gasolina`:number, `gastoPublico`:number, `inflacao`:number, `jurosDivida`:number, `petroleo`:number, `pibIndice`:number, `pibNominal`:number, `primario`:number, `produtividade`:number, `reservas`:number, `riscoPais`:number, `selic`:number, `tributosNoCaixa`:object, `tributosNoCaixa.faixas`:object, `tributosNoCaixa.faixas.alta`:number, `tributosNoCaixa.faixas.baixa`:number, `tributosNoCaixa.faixas.media`:number, `tributosNoCaixa.setores`:object, `tributosNoCaixa.setores.agro`:number, `tributosNoCaixa.setores.comercio`:number, `tributosNoCaixa.setores.digital`:number, `tributosNoCaixa.setores.financeiro`:number, `tributosNoCaixa.setores.industria`:number



## Partido — `estado.partidos.[]`

`bancadasFortes.[]`:string, `eixos.ambiental`:number, `eixos.autoridade`:number, `eixos.economico`:number, `eixos.federalismo`:number, `eixos.social`:number, `senadoPorUf.AC`:number, `senadoPorUf.AL`:number, `senadoPorUf.AM`:number, `senadoPorUf.AP`:number, `senadoPorUf.BA`:number, `senadoPorUf.CE`:number, `senadoPorUf.DF`:number, `senadoPorUf.ES`:number, `senadoPorUf.GO`:number, `senadoPorUf.MA`:number, `senadoPorUf.MG`:number, `senadoPorUf.MS`:number, `senadoPorUf.MT`:number, `senadoPorUf.PA`:number, `senadoPorUf.PB`:number, `senadoPorUf.PE`:number, `senadoPorUf.PI`:number, `senadoPorUf.PR`:number, `senadoPorUf.RJ`:number, `senadoPorUf.RN`:number, `senadoPorUf.RO`:number, `senadoPorUf.RR`:number, `senadoPorUf.RS`:number, `senadoPorUf.SC`:number, `senadoPorUf.SE`:number, `senadoPorUf.SP`:number, `senadoPorUf.TO`:number



## Supremo (STF) — `estado.supremo`

`agenda`:object, `agenda.audienciasEm`:array, `agenda.emissarioEm`:array, `agenda.mandato`:number, `balanca`:object, `balanca.arcosVividos`:array, `balanca.congressoSupremo`:number, `balanca.movimentos`:array, `balanca.planaltoCongresso`:number, `balanca.planaltoSupremo`:number, `coesao`:number, `corte`:array, `corte.[]`:object, `corte.[].deferencia.executivo`:number, `corte.[].deferencia.legislativo`:number, `corte.[].eixos.ativismo`:number, `corte.[].eixos.costumes`:number, `corte.[].eixos.economia`:number, `corte.[].eixos.federalismo`:number, `corte.[].eixos.garantismo`:number, `corte.[].indicadoPor.jogador`:boolean, `corte.[].indicadoPor.nome`:string, `corte.[].indicadoPor.partido`:string, `corte.[].nascimento.ano`:number, `corte.[].nascimento.mes`:number, `corte.[].posse.ano`:number, `corte.[].posse.mes`:number, `corte.[].tracos.articulacao`:number, `corte.[].tracos.corporativismo`:number, `corte.[].tracos.imprevisibilidade`:number, `corte.[].tracos.independencia`:number, `corte.[].tracos.midiatico`:number, `corte.[].tracos.vaidade`:number, `escandalos`:array, `historico`:array, `indicacoes`:array, `inqueritos`:array, `ordens`:array, `pauta`:array, `pendentes`:array, `pgr`:object, `pgr.ate`:object, `pgr.ate.mandato`:number, `pgr.ate.turno`:number, `pgr.desde`:object, `pgr.desde.mandato`:number, `pgr.desde.turno`:number, `pgr.genero`:string, `pgr.id`:string, `pgr.independencia`:number, `pgr.indicadoPeloJogador`:boolean, `pgr.listaTriplice`:boolean, `pgr.nome`:string, `pgr.real`:boolean, `precedentes`:array, `presidencia`:object, `presidencia.desde`:object, `presidencia.desde.ano`:number, `presidencia.desde.mes`:number, `presidencia.presidenteId`:string, `presidencia.viceId`:string, `prestigio`:number, `tse`:object, `tse.doStf`:array, `tse.doStf.[]`:object, `tse.doStf.[].ate.ano`:number, `tse.doStf.[].ate.mes`:number, `tse.doStf.[].desde.ano`:number, `tse.doStf.[].desde.mes`:number, `tse.juristas`:array



## Vida pessoal do presidente — `estado.pessoal`

`acontecimentoAtual`:null, `amigos`:array, `amigos.[]`:object, `aprovacaoPessoal`:number, `conjuge`:object, `conjuge.aprovacao`:number, `conjuge.atrito`:number, `conjuge.influencia`:number, `conjuge.nome`:string, `conjuge.papel`:string, `contaPessoal`:number, `energia`:number, `estresse`:number, `filhos`:array, `habitos`:array, `humor`:number, `patrimonio`:number, `patrimonioOculto`:number, `riscoPf`:number, `salarioMensal`:number, `saude`:number, `vividos`:array



## Presidente (personagem) — `estado.presidente`

`candidatoId`:string, `carreira`:string, `eixos`:object, `eixos.ambiental`:number, `eixos.autoridade`:number, `eixos.economico`:number, `eixos.federalismo`:number, `eixos.social`:number, `estadoNatal`:string, `formacao`:string, `genero`:string, `idade`:number, `nome`:string, `origem`:string, `partido`:string, `partidoProprio`:boolean, `partidoVice`:string, `religiao`:string, `semente`:number, `tracos`:array, `tracos.[]`:string, `vice`:string



## Oposição — `estado.oposicao`

`acoes`:array, `coesao`:number, `estrategia`:string, `forca`:number, `objetivos`:array, `turnoEstrategia`:number



## Ministérios (um ministro por pasta) — `estado.ministros`

`agricultura`:string, `casa_civil`:string, `defesa`:string, `desenvolvimento_social`:string, `educacao`:string, `fazenda`:string, `infraestrutura`:string, `justica`:string, `relacoes_exteriores`:string, `saude`:string



## Chamadas `/api/` observadas

| Método | Rota | Corpo → resposta |
| --- | --- | --- |
| GET | `/api/ranking?quadro=…` | → `linhas[]` |
| POST | `/api/ia/avaliar2026` | `{cena, partidaId, pergunta, quem, texto}` → `{evasiva, leitura, nota}` |
| POST | `/api/ia/debate2026` | `{fase, n, partidaId, texto, [alvoId, flanco]}` → `{custo, modelo, replica\|resposta, tokens}` |
| POST | `/api/partida` | `{auto, estado{…}}` → `{ok, partida{ano, aprovacao, atualizada, auto, criada, fase, id, mes, nome, partido, presidente, regime, semana, turno}}` |
