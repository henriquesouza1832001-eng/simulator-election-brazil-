# Roadmap do simulador

## Base implementada

- Estado de jogo salvo localmente no SQLite; migracoes preservam partidas existentes.
- Calendario diario, passagem de semana/mes, eventos, votacoes e maturacao de investimentos.
- Orcamento com receitas por grupo, despesas obrigatorias, compras e contratos, investimentos e custos operacionais.
- Resultado primario, juros, resultado nominal, estoque da divida, credibilidade fiscal e risco-pais calculados pelo motor.
- Viagens oficiais e residencias entram no gasto; cortes recorrentes atualizam o resultado fiscal.
- Visitas diplomaticas consomem o teto anual de viagens e alteram relacoes bilaterais.
- Agenda multilateral com eventos simulados, janela de participacao, custo e efeito de influencia.
- Painel permite escolher indicadores, incluindo resultado nominal, risco-pais e credibilidade fiscal.

## Proximas etapas

1. Separar campanhas e saves, mantendo a partida atual intacta.
2. Ligar cada investimento ministerial a uma fonte, execucao anual e entrega mensuravel.
3. Implementar partidos, bancadas, coalizoes, comissoes e votacoes com apoio por partido.
4. Expandir eventos climaticos, economicos, sociais e internacionais, com efeitos persistentes e respostas variadas.
5. Completar campanha e carreira politica com dados eleitorais do TSE e fontes verificaveis.
6. Usar IA/RAG para contexto e narrativa; o motor Python continua calculando efeitos e limites.
7. Adicionar historico do mandato, exportacao/importacao, ajuda e onboarding.

## Limites do modelo fiscal atual

Os valores de referencia sao abstracoes do simulador, nao uma reproducao da LOA ou do Siafi. A conta separa fluxos anuais, mas ainda precisa de execucao mensal detalhada, vinculos legais, transferencias entre entes e amortizacao explicita da divida.
