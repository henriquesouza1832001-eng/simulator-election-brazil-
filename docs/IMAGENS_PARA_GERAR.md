# Imagens para gerar (pedir ao GPT)

Tudo que o jogo precisa de imagem real está aqui, com o nome exato do arquivo, o tamanho e o pedido pronto para colar.
Sem a imagem, o jogo usa a arte em SVG e funciona normalmente. **Comece pela primeira.**

Regras comuns a todas (cole junto com cada pedido):

> Ilustração editorial plana com textura leve de papel, sem texto, sem letras, sem logotipos, sem rostos reconhecíveis de pessoas reais, sem bandeiras com escudos. Paleta: azul-marinho profundo (#0d1a2c), azul céu (#2a6fa8), amarelo ouro (#ffd23f), verde bandeira (#1f7a4a) e branco gelo. Estilo de cartaz de jornal moderno, traços limpos, contraste alto. Deixe o terço esquerdo da imagem mais calmo (poucos detalhes), porque um título será colocado ali.

Formato de entrega: **WebP**, 21:9, **2560 x 1100**, até 250 KB (converta em squoosh.app se vier maior). Salvar em `public/assets/hero/`.

## 1. `hero-painel-calmo.webp` (peça esta primeiro)

> Esplanada dos Ministérios em Brasília ao amanhecer, vista de frente e levemente de baixo: as duas torres do Congresso ao centro, a cúpula e a cuia, os blocos dos ministérios em fila até o horizonte. Céu em degradê do azul-marinho ao azul céu, sol dourado grande e baixo à direita. Gramado verde bandeira no primeiro plano. Clima de dia tranquilo e esperançoso.

## 2. `hero-painel-tenso.webp`

> A mesma Esplanada dos Ministérios, mesmo enquadramento da imagem 1, mas no fim da tarde: céu azul-acinzentado com nuvens pesadas, sol ouro apagado atrás das nuvens, luz fria e baixa. Poucas pessoas pequenas ao longe. Clima de alerta, sem perigo explícito.

## 3. `hero-painel-crise.webp`

> A mesma Esplanada dos Ministérios, mesmo enquadramento, ao anoitecer: céu roxo escuro e vinho, sol vermelho-coral parcialmente coberto, raio fino ao longe, edifícios em silhueta azul-marinho com poucas janelas acesas. Clima de crise, dramático, mas sem violência nem fogo.

## Como instalar

1. Salve os três arquivos em `public/assets/hero/` com **esses nomes exatos**.
2. Não precisa mexer em código: se o arquivo existe, ele substitui a arte; se não existe, a arte padrão continua.
3. Me avise e eu confiro o enquadramento e o contraste do título sobre a imagem.

## Próximas imagens (só quando a gente chegar nessas telas; não peça agora)

- `hero-governo.webp`, `hero-politica.webp`, `hero-agenda.webp`: um cabeçalho por seção, mesma família da imagem 1.
- `hero-fim-mandato.webp`: Esplanada ao entardecer com a faixa presidencial vazia sobre uma cadeira (sem rosto).
