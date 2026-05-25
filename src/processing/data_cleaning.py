"""Data processing and cleaning for parliamentary network construction."""
import pandas as pd # type: ignore
import logging
from typing import List, Tuple
from models.deputy import Deputy
from models.proposition import Proposition
from models.coauthorship_edge import CoauthorshipEdge

class ChamberProcessor:
    """Processes raw parliamentary data into domain objects."""

    def __init__(self, debug: bool = True) -> None:
        self.logger = self._setup_logger()
        self.raw_dataframe = None
        self.clean_dataframe = None
        self.deputies: List[Deputy] = []
        self.propositions: List[Proposition] = []
        self.edges: List[CoauthorshipEdge] = []

    def _setup_logger(self) -> logging.Logger:
        """Configure logging for data processing and return logger."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(handler)
        return logger

    def process_raw_data(self, raw_df: pd.DataFrame, propositions_df: pd.DataFrame, proposition_filter=['PL', 'PEC', 'PLP', 'PDL', 'EMC'], max_authors: int = 30):
        # 1. Padronização
        df_authors = raw_df.copy()
        df_props = propositions_df.copy()

        df_authors.columns = [c.strip().lower() for c in df_authors.columns]
        df_props.columns = [c.strip().lower() for c in df_props.columns]

        # 2. Filtro de Visão (Manter apenas o que tem valor político real)
        # Selecionamos apenas Projetos de Lei, Emendas à Constituição e Leis Complementares
        df_props_filtered = df_props[df_props['siglatipo'].isin(proposition_filter)]

        # 3. Cruzamento (Merge): O "filtro atômico"
        # O inner join remove instantaneamente os 90 mil registros de requerimentos e ofícios
        df_merged = df_authors.merge(
            df_props_filtered[['id', 'siglatipo']], 
            left_on='idproposicao', 
            right_on='id', 
            how='inner'
        )

        type_map = df_merged.drop_duplicates('idproposicao').set_index('idproposicao')['siglatipo'].to_dict()

        # 2. Filtros de Domínio (Só Deputados Federais)
        df_deputies = df_merged[df_merged['codtipoautor'] == 10000].copy()
        df_deputies = df_deputies.dropna(subset=['iddeputadoautor'])
        df_deputies['iddeputadoautor'] = df_deputies['iddeputadoautor'].astype(int)

        # 3. Metadados dos Nós (Vértices)
        df_meta = df_deputies.drop_duplicates(subset=['iddeputadoautor'], keep='last')
        deputy_map = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

        # 4. Agrupamento (Arestas)
        groups = df_deputies.groupby('idproposicao')['iddeputadoautor'].apply(list)
        coauthorships = groups[groups.apply(len) > 1]

        # 5. Mass-signature filter: exclude proposals whose author count exceeds
        # max_authors. A single PEC with 200+ signatories creates O(n²) pairs
        # and drives edge density above 85%, making community detection invalid.
        coauthorships = coauthorships[coauthorships.apply(len) <= max_authors]

        return deputy_map, groups, coauthorships, type_map
    
    def process_raw_data_unfiltered(self, raw_df: pd.DataFrame):
        """Process raw data without filtering proposition types.

        Returns deputy_map, groups, coauthorships
        """
        df = raw_df.copy()
        df.columns = [c.strip().lower() for c in df.columns]

        df_deputies = df[df['codtipoautor'] == 10000].copy()
        df_deputies = df_deputies.dropna(subset=['iddeputadoautor'])
        df_deputies['iddeputadoautor'] = df_deputies['iddeputadoautor'].astype(int)

        df_meta = df_deputies.drop_duplicates(subset=['iddeputadoautor'], keep='last')
        deputy_map = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

        groups = df_deputies.groupby('idproposicao')['iddeputadoautor'].apply(list)
        coauthorships = groups[groups.apply(len) > 1]

        return deputy_map, groups, coauthorships
    
    def convert_to_domain_objects(
        self,
        deputy_map: dict,
        groups: pd.Series,
        coauthorships: pd.Series,
        type_map: dict,
        year: int
    ) -> tuple:
        """Convert raw data maps to domain objects.
        
        Args:
            deputy_map: Mapping of deputy_id -> metadata
            groups: Grouping of deputies by proposition ID
            coauthorships: Filtered groups with 2+ authors
            type_map: Mapping of proposition_id -> proposition_type
            year: Analysis year
            
        Returns:
            Tuple of (deputies_dict, propositions_list, coauthorships_list)
        """
        # 1. Create Deputy objects (nodes)
        deputies_dict = {}
        for deputy_id, info in deputy_map.items():
            deputies_dict[deputy_id] = Deputy(
                id=deputy_id,
                name=info['nomeautor'],
                party_code=info['siglapartidoautor'],
                state_code=info['siglaufautor']
            )
        
        # 2. Co-authorship propositions only (edges subset)
        coauthorships_list = []
        for prop_id, author_ids in coauthorships.items():
            coauthorships_list.append(Proposition(
                id=prop_id,
                year=year,
                author_ids=author_ids,
                proposition_type=type_map.get(prop_id, "N/A")
            ))
        
        # 3. All propositions (individual + collective)
        propositions_list = []
        for prop_id, author_ids in groups.items():
            propositions_list.append(Proposition(
                id=prop_id,
                year=year,
                author_ids=author_ids,
                proposition_type=type_map.get(prop_id, "N/A")
            ))
        
        return deputies_dict, propositions_list, coauthorships_list