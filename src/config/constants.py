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

# Maximum number of deputy co-authors allowed per proposal.
# Proposals above this threshold (mass-signature petitions, full-bench
# constitutional amendments, etc.) are excluded from the co-authorship
# graph because they generate O(n²) edges — a PEC with 226 signatories
# alone creates ~25 k pairs, driving edge density above 85% and making
# community detection scientifically meaningless.
# Tune this value and report sensitivity in the monograph (advisor feedback).
MAX_AUTHORS_PER_PROPOSAL = 30

# Community detection parameters
NUM_COMMUNITIES = 5
COMMUNITY_DETECTION_METHOD = 'spectral'  # spectral, louvain, greedy

# ---------------------------------------------------------------------------
# Proposition type weights
# ---------------------------------------------------------------------------
# All included proposition types receive a uniform weight of 1.
#
# Rationale (advisor feedback, Rubens Barbosa Filho): assigning different
# numerical weights to proposition types (e.g. PL > PEC) is inherently
# arbitrary — no established theoretical basis exists in the literature for
# such a scale. The type *filter* (which types enter the graph at all) already
# encodes the analytical decision of which propositions are politically
# meaningful. Beyond that filter, treating every co-authorship equally is the
# most parsimonious and reproducible choice.
#
# Consequently, edge weight reflects only the normalized count of co-authored
# propositions: w(i,j) = Σ 1/(n_authors(p) − 1) for each shared proposal p.
#
# If a future study wishes to explore weighted variants, this dict can be
# overridden via the ``proposition_weights`` constructor argument of
# ``ParliamentaryGraph`` without changing any other code.
PROPOSITION_TYPE_WEIGHTS: dict[str, float] = {
    'PL':  1,    # Bill (Lei Ordinária)
    'PLP': 1,    # Complementary Law Bill
    'PEC': 1,    # Constitutional Amendment Proposal
    'PLV': 1,    # Provisional-measure conversion bill
    'PDL': 1,    # Legislative Decree
    'EMC': 1,    # Committee amendment
}

# ---------------------------------------------------------------------------
# Deputy ID aliases
# ---------------------------------------------------------------------------
# Some deputies appear in the Chamber's open-data CSVs under more than one
# numeric ID. The CSV for the 2025 piloto run, for instance, contains a
# "phantom" entry (id=130398) that actually refers to deputy André Fernandes
# (active id=220657). This mapping collapses such duplicates so that the
# network treats them as a single node. Add new entries here as they are
# identified during data validation; the value is the canonical (active) ID.
DEPUTY_ID_ALIASES: dict[int, int] = {
    130398: 220657,  # André Fernandes — phantom ID observed in 2025 CSV
}
