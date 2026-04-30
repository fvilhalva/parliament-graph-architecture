"""Shared test fixtures for all test modules."""
import pytest # type: ignore
from models.deputy import Deputy
from models.proposition import Proposition
from models.coauthorship_edge import CoauthorshipEdge


@pytest.fixture
def deputy_silva():
    """Create a deputy for testing."""
    return Deputy(
        id=1,
        name="João Silva",
        party_code="PT",
        state_code="SP",
        degree_centrality=0.5,
        betweenness_centrality=0.3
    )


@pytest.fixture
def deputy_santos():
    """Create another deputy for testing."""
    return Deputy(
        id=2,
        name="Maria Santos",
        party_code="PSDB",
        state_code="MG",
        degree_centrality=0.6,
        betweenness_centrality=0.4
    )


@pytest.fixture
def deputy_oliveira():
    """Create a third deputy for testing."""
    return Deputy(
        id=3,
        name="Carlos Oliveira",
        party_code="PT",
        state_code="RJ",
        degree_centrality=0.4,
        betweenness_centrality=0.2
    )


@pytest.fixture
def proposition_example():
    """Create a proposition for testing."""
    return Proposition(
        id=100,
        year=2024,
        author_ids=[1, 2, 3],
        proposition_type="PL"
    )


@pytest.fixture
def proposition_other():
    """Create another proposition for testing."""
    return Proposition(
        id=101,
        year=2024,
        author_ids=[1, 2],
        proposition_type="PEC"
    )


@pytest.fixture
def coauthorship_edge():
    """Create a coauthorship edge for testing."""
    return CoauthorshipEdge(
        source_id=1,
        target_id=2,
        raw_weight=5,
        normalized_strength=0.8
    )


# --- Portuguese alias fixtures for backward compatibility ---

@pytest.fixture
def deputado_silva(deputy_silva):
    """Portuguese alias for deputy_silva fixture."""
    return deputy_silva


@pytest.fixture
def proposicao_exemplo(proposition_example):
    """Portuguese alias for proposition_example fixture."""
    return proposition_example


@pytest.fixture
def proposicao_outro(proposition_other):
    """Portuguese alias for proposition_other fixture."""
    return proposition_other


@pytest.fixture
def aresta_coautoria(coauthorship_edge):
    """Portuguese alias for coauthorship_edge fixture."""
    return coauthorship_edge


@pytest.fixture
def example_deputies(deputy_silva, deputy_santos, deputy_oliveira):
    """Create list of deputies for testing."""
    return [deputy_silva, deputy_santos, deputy_oliveira]


@pytest.fixture
def deputados_exemplo(example_deputies):
    """Portuguese alias for example_deputies fixture."""
    return example_deputies
