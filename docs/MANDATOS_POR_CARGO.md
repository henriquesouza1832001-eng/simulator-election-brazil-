# Mandatos por cargo

## O que entrou nesta etapa

Partidas em mandato agora mostram uma aba própria com o nome da instituição ou do Executivo que o personagem ocupa. A tela resume território, recursos, entregas, atribuições e limites do cargo. Os painéis usam os dados já existentes em `career_overview`; o React apresenta os valores e o motor Python continua decidindo custos, prazos e efeitos.

| Cargo | Aba e foco | Recursos/ações já simulados |
| --- | --- | --- |
| Vereador(a) | Câmara municipal: leis locais, orçamento e fiscalização da prefeitura | Capital político; proposta municipal, fiscalização de serviço local e audiência com moradores |
| Prefeito(a) | Prefeitura: serviços e prioridades da cidade | Reserva municipal dimensionada pela população; programas locais de educação, saúde, mobilidade, saneamento e emprego |
| Deputado(a) estadual | Assembleia Legislativa: leis estaduais e controle do Executivo | Capital político; projeto estadual, fiscalização de programa estadual e audiência na Assembleia |
| Governador(a) | Governo estadual: serviços, segurança e infraestrutura | Reserva estadual dimensionada pela população; programas estaduais, inclusive segurança e infraestrutura |
| Deputado(a) federal | Câmara dos Deputados: legislação federal, orçamento e fiscalização | Capital político; projeto federal, fiscalização de ministérios e audiência em comissão |
| Senador(a) | Senado: representação estadual e decisões nacionais | Capital político; projeto com prazo de tramitação maior, fiscalização do Executivo e audiência nacional |
| Presidente(a) | Presidência: coordenação do Executivo federal | Carteira federal de investimentos; programas nacionais, crise, orçamento, nomeações e diplomacia nas abas próprias |

## Regras preservadas

- As opções de ação vêm do motor e são verificadas novamente pelo servidor ao executar.
- O calendário limita decisões de mandato; programas executivos reservam recursos e têm prazo de entrega.
- Mandatos legislativos gastam capital político, registram propostas ou fiscalizações na carteira e não recebem controles diretos de serviços do Executivo.
- Território, atribuições e limites são mostrados como regras desta simulação. Os valores não substituem dados oficiais de orçamento ou execução.

## Próximo aprofundamento para revisão com Claude

O painel já diferencia as sete funções e os instrumentos legislativos por casa. Para ampliar os sistemas depois da revisão visual, implementar em etapas: tramitação com comissões e votação nominal; emendas orçamentárias por esfera; carteira e contratos estaduais/municipais; secretarias e relação com as respectivas casas legislativas. Cada nova ação precisa de custo ou recurso, prazo, resultado observável e limite institucional explícito.
