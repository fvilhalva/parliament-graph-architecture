"""Constantes do domínio"""

# Partidos
# Partidos que elegeram deputados (2006-2026)
PARTIDOS = [
    # Principais (sempre representados)
    'PT', 'PSD', 'MDB', 'PP', 'PL', 'PSB', 'PSDB', 'REPUBLICANOS',
    'PDT', 'SOLIDARIEDADE', 'AVANTE', 'PODEMOS', 'AGIR', 'NOVO',
    
    # Representados em períodos específicos
    'PCdoB', 'DEM', 'PHS', 'PMN', 'PV', 'PRB', 'PTB', 'PROS',
    'PATRI', 'UNIÃO', 'Federação'
]

# Estados
ESTADOS = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

# Limites de análise
MIN_COAUTORIAS = 2 # ajustavel e bom para ver aliados principais, todos, significativas
MIN_PESO_ARESTA = 1

# Clustering
NUM_COMUNIDADES = 5
METODO_COMUNIDADES = 'spectral'  # spectral, louvain, greedy