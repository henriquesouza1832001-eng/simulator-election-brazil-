# Personagem e retratos

## Entrada da partida

A tela oferece dois caminhos separados: posse direta na Presidência em 1º de janeiro de 2027 ou carreira eleitoral com escolha de cargo, estado e município. Ambos pedem um nome e um perfil fictício.

Na carreira, espectro político e origem familiar aplicam pequenas mudanças na base inicial dos grupos. Os traços têm efeitos descritos na própria tela e são aplicados pelo motor. Costumes e biografia ficam salvos no perfil, sem bônus numéricos por enquanto. Na posse direta, os traços escolhidos ajustam os indicadores iniciais e o nome do personagem aparece no painel.

## Retratos

O repositório ainda não contém fotos oficiais de candidatos nem caricaturas de políticos. O TSE disponibiliza arquivos de fotos vinculados aos conjuntos de candidaturas; cada importação deve manter ano, UF, identificador da candidatura, origem, licença e atribuição.

Fotos documentais e caricaturas são tipos diferentes no catálogo `public/assets/portraits/catalog.json`. Caricaturas precisam registrar a referência usada, data de geração e aviso de sátira. O esquema de metadados está em `public/assets/portraits/catalog.schema.json`.

O objetivo de cobertura de 1.000–1.200 figuras fica para uma etapa de importação e seleção do elenco: usar a foto oficial como referência não cria, por si só, uma caricatura. O primeiro lote deve ser definido pelo elenco jogável (Presidência, ministérios, Congresso, governos estaduais e candidaturas competitivas), para evitar gerar milhares de imagens sem uso nas telas.
