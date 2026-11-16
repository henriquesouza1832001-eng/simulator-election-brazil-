# Imagens que faltam para o jogo ficar completo

Complementa `IMAGENS_PARA_GERAR.md` (o bloco de estilo que gerou as sete imagens de cabeçalho que você aprovou). **Use sempre aquele bloco de estilo primeiro, na mesma conversa.** Aqui estão as 53 imagens restantes, com nome de arquivo, tamanho e pedido.

## Situação hoje

- **Aba Projetos:** já usa cartões com arte própria em SVG (no mesmo estilo). A imagem real, quando existir, substitui a arte sozinha.

- Prontas e no repositório: `hero-painel-calmo`, `hero-painel-tenso`, `hero-painel-crise` (já aparecem no Painel), `hero-governo`, `hero-politica`, `hero-agenda`, `hero-fim-mandato` (prontas, ainda **não ligadas** a nenhuma tela).
- O jogo troca de arte sem mexer em código: se o arquivo existe com o nome certo, ele aparece; se não, fica a arte padrão em SVG.

## O que muda no estilo para crises

O bloco de estilo proíbe fogo e violência. Para os cartões de crise, **acrescente** este parágrafo depois do bloco:

> Variante de crise: o clima é grave, mas respeitoso. Mostre o lugar e a ameaça como formas simples (lama, água, fumaça, encosta, céu carregado) vistos de longe, sem pessoas, sem vítimas, sem destroços detalhados, sem chamas nítidas (incêndio vira só brilho laranja no céu e silhueta). Paleta: pode usar vermelho-coral `#e2554a` e vinho `#4a1d3a` em até um quarto da imagem. Mantenha o grão de papel e as formas planas.

## Formatos

| Tipo | Tamanho | Peso | Pasta |
|---|---|---|---|
| Cabeçalho de seção | 2560 x 1100 (21:9), terço esquerdo calmo | até 250 KB | `public/assets/hero/` |
| Cartão (crise, projeto, cargo, partida) | 1280 x 800 (16:10), assunto no centro | até 120 KB | `public/assets/cards/` |
| Fundo de região | 2560 x 1100 | até 220 KB | `public/assets/regions/` |

Todos em WebP. Nunca texto, letras, números, logotipos nem rosto reconhecível.

## A. Cabeçalhos por seção (9)

Nome: `hero-<seção>-calmo.webp` (variantes `-tenso` e `-crise` só no Painel, que já tem).

| Arquivo | Cena |
|---|---|
| `hero-projetos-calmo` | Canteiro de obra monumental ao amanhecer visto de longe: guindastes, uma ponte em construção e uma rodovia em curva, tudo em formas simples |
| `hero-congresso-calmo` | O plenário vazio visto de cima, fileiras em arco, luz entrando por uma abertura |
| `hero-eleicao-calmo` | Fila de urnas eletrônicas (só o objeto, sem marca) sobre uma mesa, luz de manhã de domingo |
| `hero-apuracao-calmo` | Parede grande de telões com um mapa do Brasil abstrato aceso em manchas azuis e douradas, sala escura, sem números |
| `hero-entrevistas-calmo` | Estúdio de TV vazio: duas poltronas, mesa, microfones, luz de cenário, sem logotipo |
| `hero-redes-calmo` | Vários celulares flutuando em arco, telas como retângulos de cor sem conteúdo legível |
| `hero-economia-calmo` | Fachada de um prédio de banco central genérico, colunas, escadaria, céu limpo |
| `hero-diplomacia-calmo` | Palácio com arcos refletidos num espelho d'água, bandeiras sem escudo como faixas de cor |
| `hero-territorio-calmo` | O mapa do Brasil como relevo de papel em camadas, com rios em ouro |

## B. Cartões de crise (12) · variante de crise

Nome: `cards/crise-<id>.webp`.

| Arquivo | Cena (sempre de longe, sem pessoas) |
|---|---|
| `crise-barragem` | Vale ao entardecer com uma barragem de rejeito e uma mancha de lama marrom avançando em formas planas |
| `crise-enchente` | Rua de cidade do Sul com água até a altura das portas, telhados e postes, céu cinza-azulado |
| `crise-deslizamento` | Encosta urbana com casas simples e uma cicatriz de terra caída, chuva em linhas finas |
| `crise-seca` | Sertão rachado, açude quase vazio, céu amarelo duro, uma árvore seca |
| `crise-queimada` | Cerrado ao fim do dia com céu laranja e fumaça em camadas, só o brilho no horizonte |
| `crise-pandemia` | Corredor de hospital de campanha com fileiras de leitos vazios e tendas, luz fria |
| `crise-apagao` | Cidade à noite com a maior parte dos prédios apagados e só algumas janelas acesas |
| `crise-greve-caminhoneiros` | Rodovia reta com uma longa fila de caminhões parados, céu ao amanhecer |
| `crise-crise-bancaria` | Fachada de banco com as portas fechadas e a escadaria vazia, cor fria |
| `crise-crise-hidrica` | Represa com a marca do nível antigo bem acima da água |
| `crise-epidemia` | Fila de macas de rua e tendas de vacinação sem pessoas, luz de fim de tarde |
| `crise-tempestade` | Orla de cidade litorânea com mar agitado e nuvens pesadas |

## C. Cartões de projeto e obra (14)

Nome: `cards/obra-<id>.webp`. Estilo normal, luz de dia.

`obra-rodovia`, `obra-ferrovia`, `obra-ponte`, `obra-viaduto`, `obra-porto`, `obra-aeroporto`, `obra-hidrovia`, `obra-metro`, `obra-saneamento`, `obra-habitacao`, `obra-escola`, `obra-hospital`, `obra-energia`, `obra-reforma-urbana`.

Cena de cada uma: o próprio tipo de obra, em construção e em operação lado a lado (metade esquerda em andaime e guindaste, metade direita pronta), sem pessoas.


## C2. Nomes exatos por projeto (37)

O jogo procura `public/assets/cards/obra-<id>.webp` para cada projeto. Enquanto o arquivo não existe, aparece a arte em SVG. Esta tabela substitui a lista genérica da seção C.

| Arquivo | Projeto | Tipo |
|---|---|---|
| `obra-br116_sul.webp` | Corredor rodoviário Sul-Sudeste | Rodovia |
| `obra-fioleste.webp` | Ferrovia de Integração Leste-Oeste | Ferrovia |
| `obra-hidrovia_tocantins.webp` | Hidrovia Tocantins-Araguaia | Hidrovia |
| `obra-hidrovia_paraguai.webp` | Hidrovia do Paraguai | Hidrovia |
| `obra-porto_santos.webp` | Acesso ferroviário e portuário de Santos | Porto e ferrovia |
| `obra-saneamento_norte.webp` | Saneamento e drenagem de cidades do Norte | Saneamento |
| `obra-ponte_amazonica.webp` | Ponte da Integração Amazônica | Ponte |
| `obra-viaduto_metropolitano.webp` | Viadutos e alças do anel metropolitano | Viaduto |
| `obra-anel_rodoviario.webp` | Anel rodoviário da capital | Rodovia |
| `obra-metro_capital.webp` | Metrô de capital metropolitana | Metrô |
| `obra-brt_corredores.webp` | Corredores de ônibus de alta capacidade | BRT |
| `obra-aeroporto_regional.webp` | Aeroporto internacional regional | Aeroporto |
| `obra-porto_aguas_profundas.webp` | Porto de águas profundas | Porto |
| `obra-ferrovia_do_grao.webp` | Ferrovia do Grão | Ferrovia |
| `obra-drenagem_sul.webp` | Drenagem urbana e contenção de enchentes | Drenagem |
| `obra-adutoras_semiarido.webp` | Adutoras e dessalinização do Semiárido | Água |
| `obra-habitacao_popular.webp` | Habitação popular em larga escala | Habitação |
| `obra-retrofit_predios.webp` | Reforma e eficiência dos prédios públicos | Reforma |
| `obra-centros_historicos.webp` | Revitalização de centros históricos | Reforma |
| `obra-hospitais_regionais.webp` | Hospitais federais regionais | Hospital |
| `obra-rede_upas.webp` | Rede de UPAs e policlínicas | Hospital |
| `obra-complexo_vacinas.webp` | Complexo industrial de vacinas e insumos | Indústria |
| `obra-escolas_tempo_integral.webp` | Escolas em tempo integral | Escola |
| `obra-creches.webp` | Creches e pré-escolas | Escola |
| `obra-universidades_interior.webp` | Universidades e institutos no interior | Universidade |
| `obra-fronteira_integrada.webp` | Monitoramento integrado da fronteira | Defesa |
| `obra-presidios_federais.webp` | Sistema penitenciário federal ampliado | Presídio |
| `obra-usina_hidreletrica.webp` | Usina hidrelétrica de grande porte | Energia |
| `obra-eolica_offshore.webp` | Parque eólico no mar | Energia |
| `obra-linhao_transmissao.webp` | Linhão de transmissão Norte-Sul | Energia |
| `obra-irrigacao_sao_francisco.webp` | Irrigação e perímetros do Rio São Francisco | Irrigação |
| `obra-alcantara_comercial.webp` | Centro de Lançamentos de Alcântara: base comercial | Espaço |
| `obra-satelites_nacionais.webp` | Constelação nacional de satélites | Espaço |
| `obra-astronauta_orbita.webp` | Programa Astronauta Brasileiro: missão em órbita | Espaço |
| `obra-missao_lunar.webp` | Missão Lunar Brasileira | Espaço |
| `obra-reator_pesquisa.webp` | Reator multipropósito de pesquisa | Ciência |
| `obra-supercomputador.webp` | Supercomputador nacional | Ciência |

## D. Cartões de cargo (7)

Nome: `cards/cargo-<id>.webp`.

| Arquivo | Cena |
|---|---|
| `cargo-vereador` | Câmara municipal pequena, fachada simples de cidade do interior |
| `cargo-prefeito` | Prefeitura com praça e coreto à frente |
| `cargo-deputado-estadual` | Assembleia legislativa estadual, escadaria |
| `cargo-deputado-federal` | Cúpula do Congresso Nacional em close, sem as torres |
| `cargo-senador` | A cúpula côncava do Senado em close |
| `cargo-governador` | Palácio de governo estadual com bandeira de faixa de cor |
| `cargo-presidente` | O Palácio do Planalto de frente, rampa e colunas |

## E. Cartões das quatro entradas de partida (4)

`cards/inicio-governo.webp` (Esplanada ao amanhecer), `inicio-campanha.webp` (rua com faixas e bandeirinhas de papel vistas de longe), `inicio-militancia.webp` (sede de partido modesta com cadeiras na calçada), `inicio-eleitor.webp` (cabine de votação vazia com cortina).

## F. Fundos de região (5)

`regions/regiao-norte.webp` (rio largo e floresta em camadas), `regiao-nordeste.webp` (litoral, coqueiros e sertão ao fundo), `regiao-centro-oeste.webp` (planalto com campo aberto e silos), `regiao-sudeste.webp` (skyline de metrópole e serra), `regiao-sul.webp` (coxilhas, araucárias e neblina).

## G. Fim de mandato (2)

`hero-fim-mandato-vitoria.webp` (Esplanada ao entardecer, céu dourado) e `hero-fim-mandato-derrota.webp` (mesma cena em azul frio). Já existe `hero-fim-mandato`.

## Como produzir com a mesma qualidade

1. Uma conversa por grupo (A, B, C…), colando primeiro o bloco de estilo e, no grupo B, também a variante de crise.
2. Gere cada imagem uma de cada vez e confira: sem texto, sem rosto, assunto no centro, terço esquerdo calmo nos cabeçalhos.
3. Converta para WebP com o peso indicado e salve na pasta com o nome exato.
4. Me avise por grupo: eu ligo cada pasta às telas (hoje só o Painel usa imagem) e confiro o contraste do texto sobre a arte.

**Gerar pelo Gemini?** A sua chave lista modelos de imagem, e eu posso montar um script em lote. Não recomendo misturar: as sete imagens aprovadas vêm de outro gerador, e o estilo muda de um modelo para o outro. Se quiser testar, o jeito seguro é gerar 3 amostras (uma de cada grupo) e comparar ao lado das aprovadas antes de gastar cota.
