# Parliament Graph Architecture
## Architecture based on graphs for detection of influence structures

# Dir format
src/
├── config/         # Lê o .env, configura os Logs do sistema
├── models/         # Classes puras: Deputado, Proposicao, Grafo
├── extraction/     # Classes de conexão HTTP: CamaraExtractor
├── processing/     # Funções de limpeza de DataFrames (Pandas)
├── core/           # Classes de Matemática: CalculadoraCentralidade
├── database/       # Classes Repository: CsvExporter, GephiExporter
└── visualization/  # Classes geradoras de gráficos (Matplotlib)