"""Domain constants for parliamentary network analysis."""

# Political parties represented in Brazilian Chamber of Deputies (2006-2026)
POLITICAL_PARTIES = [
    # Major parties (consistently represented)
    'PT', 'PSD', 'MDB', 'PP', 'PL', 'PSB', 'PSDB', 'REPUBLICANOS',
    'PDT', 'SOLIDARIEDADE', 'AVANTE', 'PODEMOS', 'AGIR', 'NOVO',
    
    # Represented in specific periods
    'PCdoB', 'DEM', 'PHS', 'PMN', 'PV', 'PRB', 'PTB', 'PROS',
    'PATRI', 'UNIÃO', 'Federação'
]

# Brazilian states by abbreviation
BRAZILIAN_STATES = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

# Analysis thresholds
# Minimum number of co-authorships to create an edge (adjustable)
# 2: main allies, all collaborators
# 3: significant collaborations
MIN_COAUTHORSHIPS = 2
MIN_EDGE_WEIGHT = 1

# Community detection parameters
NUM_COMMUNITIES = 5
COMMUNITY_DETECTION_METHOD = 'spectral'  # spectral, louvain, greedy

# Proposition types and their relative importance weights
PROPOSITION_TYPE_WEIGHTS = {
    'PL': 10,    # Bill (Lei Ordinária)
    'PLP': 5,    # Complementary Law Bill
    'PEC': 1,    # Constitutional Amendment Proposal
    'PLV': 8,    # Urgent Consideration Bill
    'PDL': 3,    # Legislative Decree
    'REQ': 1,    # Request
    'MOC': 1,    # Motion
}