# Imagens para gerar (pedir ao GPT)

Tudo que o jogo precisa de imagem real está aqui, com o nome exato do arquivo, o tamanho e o pedido pronto para colar.
Sem a imagem, o jogo usa a arte em SVG e funciona normalmente. **Comece pela primeira.**

## Como usar (3 passos)

1. Abra uma conversa nova no GPT e cole **primeiro o BLOCO DE ESTILO** abaixo. Isso fixa a família visual.
2. Na mesma conversa, cole o pedido da imagem (1, 2 e 3 em sequência). Mantendo a conversa, as três saem com o mesmo enquadramento.
3. Converta para WebP (squoosh.app) e salve em `public/assets/hero/` com o nome exato.

## BLOCO DE ESTILO (cole antes de qualquer pedido)

> Você vai criar ilustrações de cabeçalho para um jogo de simulação política brasileiro chamado "Quatro Anos". Estilo: ilustração editorial plana, como um cartaz de jornal moderno. Formas geométricas limpas, traço firme, poucas texturas (apenas um grão leve de papel), alto contraste, sem degradês fotográficos e sem aspecto de foto. Pense em capa de revista de política com arte vetorial sofisticada.
>
> Paleta obrigatória (use só estas cores e tons próximos): azul-marinho profundo `#0d1a2c`, azul médio `#15253d`, azul céu `#2a6fa8`, amarelo ouro `#ffd23f`, ouro escuro `#f5b800`, verde bandeira `#1f7a4a` (só em gramado e detalhes pequenos), branco gelo `#f3f6fb`. Nada de rosa, roxo vivo ou neon, exceto onde o pedido da imagem mandar.
>
> Regras fixas: sem texto, sem letras, sem números, sem logotipos, sem marcas d'água, sem bandeiras com escudos ou brasões, sem rostos de pessoas reais ou reconhecíveis, sem pessoas em primeiro plano (no máximo figuras minúsculas e anônimas ao longe, em silhueta). Nada de violência, fogo ou armas.
>
> Composição fixa: formato panorâmico 21:9, 2560 x 1100 px. O **terço esquerdo** da imagem deve ser calmo, com poucos detalhes e tons mais escuros, porque o título do jogo será colocado ali. O interesse visual fica nos dois terços da direita. Deixe uma faixa discreta de gramado ou chão na parte de baixo, sem detalhes que concorram com o texto. A imagem será usada como fundo, com um escurecimento por cima, então evite brancos estourados nas bordas.

## 1. `hero-painel-calmo.webp` (peça esta primeiro)

> Esplanada dos Ministérios, em Brasília, ao amanhecer. Vista frontal, câmera um pouco abaixo do horizonte, olhando ao longo do eixo monumental. Ao centro-direita, o Congresso Nacional: as duas torres gêmeas altas e finas lado a lado, a cúpula côncava (a "cuia" virada para cima) e a cúpula convexa, com a laje horizontal baixa e a rampa. À esquerda, em perspectiva, os blocos retangulares dos ministérios em fila até o horizonte, todos iguais, com fachadas lisas em azul e janelas em faixas. Céu em degradê de azul-marinho no alto para azul céu e uma faixa dourada no horizonte. Sol grande, baixo, dourado, atrás do Congresso à direita, com raios longos e suaves. Gramado verde bandeira largo no primeiro plano, com uma linha de perspectiva clara. Sombras longas e frias. Clima: dia novo, calmo e esperançoso. Terço esquerdo com céu limpo e blocos distantes, sem nada marcante.

## 2. `hero-painel-tenso.webp`

> A mesma Esplanada dos Ministérios, exatamente o mesmo enquadramento, a mesma posição do Congresso, dos blocos e do horizonte da imagem 1, mas no fim da tarde. Céu azul-acinzentado, com camadas de nuvens pesadas e achatadas cruzando a imagem; o sol ouro escuro e apagado, quase escondido atrás das nuvens, com uma fresta de luz fina. Luz fria e baixa, sombras compridas e frias no gramado. O gramado perde saturação e fica um verde mais escuro. Ao longe, três ou quatro figuras minúsculas em silhueta caminham pela Esplanada. Clima: alerta e tensão, sem perigo explícito. Terço esquerdo calmo e escuro.

## 3. `hero-painel-crise.webp`

> A mesma Esplanada dos Ministérios, o mesmo enquadramento das imagens 1 e 2, ao anoitecer. Céu em degradê de azul-marinho muito escuro para roxo escuro e vinho no horizonte. Sol vermelho-coral, grande, parcialmente coberto por uma nuvem, quase tocando a linha do horizonte. Um raio fino e distante, discreto, no lado direito do céu. Congresso e ministérios em silhueta azul-marinho quase preta, com poucas janelas acesas em amarelo ouro. Gramado em tom muito escuro, com um reflexo vermelho-coral fraco do sol. Clima: crise, dramático e pesado, mas sem violência, fogo, fumaça ou multidão. Terço esquerdo escuro e quase liso.

## Conferência antes de salvar

- As três imagens devem ter Congresso, blocos e horizonte no **mesmo lugar** (o jogo troca de uma para outra conforme o clima do governo).
- Sem texto nem letras em nenhum canto.
- Terço esquerdo calmo, sem objetos fortes (o título fica ali).
- Tamanho final: WebP, 2560 x 1100, até 250 KB. Se passar, reduza a qualidade no squoosh.app.

## Como instalar

1. Salve os três arquivos em `public/assets/hero/` com **esses nomes exatos**.
2. Não precisa mexer em código: se o arquivo existe, ele substitui a arte; se não existe, a arte padrão continua.
3. Me avise e eu confiro o enquadramento e o contraste do título sobre a imagem.

## Próximas imagens (só quando a gente chegar nessas telas; não peça agora)

- `hero-governo.webp`, `hero-politica.webp`, `hero-agenda.webp`: um cabeçalho por seção, mesma família da imagem 1.
- `hero-fim-mandato.webp`: Esplanada ao entardecer com a faixa presidencial vazia sobre uma cadeira (sem rosto).
