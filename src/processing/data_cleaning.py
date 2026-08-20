"""Data processing and cleaning for parliamentary network construction."""
import logging

import pandas as pd  # type: ignore

from models.deputy import Deputy
from models.proposition import Proposition

# Proposition types kept in the co-authorship graph — the qualitative filter that
# selects politically substantive matters (bills, constitutional amendments,
# complementary bills, legislative decrees and committee amendments).
DEFAULT_PROPOSITION_TYPES = ("PL", "PEC", "PLP", "PDL", "EMC")


class ChamberProcessor:
    """Processes raw parliamentary data into domain objects."""

    def __init__(self, debug: bool = True) -> None:
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure logging for data processing and return logger."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(handler)
        return logger

    def process_raw_data(self, raw_df: pd.DataFrame, propositions_df: pd.DataFrame, proposition_filter=None, max_authors: int = 30):
        # ``None`` default (instead of a mutable list literal) avoids the shared
        # default-argument pitfall.
        if proposition_filter is None:
            proposition_filter = list(DEFAULT_PROPOSITION_TYPES)

        # 1. Column standardisation
        df_authors = raw_df.copy()
        df_props = propositions_df.copy()

        df_authors.columns = [c.strip().lower() for c in df_authors.columns]
        df_props.columns = [c.strip().lower() for c in df_props.columns]

        # 2. Type filter: keep only politically substantive proposition types.
        df_props_filtered = df_props[df_props['siglatipo'].isin(proposition_filter)]

        # 3. Merge (the "atomic filter"): the inner join instantly drops the tens
        # of thousands of requirements and administrative records that are not in
        # the selected proposition types.
        df_merged = df_authors.merge(
            df_props_filtered[['id', 'siglatipo']],
            left_on='idproposicao',
            right_on='id',
            how='inner',
        )

        type_map = df_merged.drop_duplicates('idproposicao').set_index('idproposicao')['siglatipo'].to_dict()

        # 4. Domain filter: keep only federal deputies (author type code 10000).
        df_deputies = df_merged[df_merged['codtipoautor'] == 10000].copy()
        df_deputies = df_deputies.dropna(subset=['iddeputadoautor'])
        df_deputies['iddeputadoautor'] = df_deputies['iddeputadoautor'].astype(int)

        # 5. Node metadata (vertices).
        df_meta = df_deputies.drop_duplicates(subset=['iddeputadoautor'], keep='last')
        deputy_map = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

        # 6. Grouping into co-authorship sets (edges).
        groups = df_deputies.groupby('idproposicao')['iddeputadoautor'].apply(list)
        coauthorships = groups[groups.apply(len) > 1]

        # 7. Mass-signature filter: exclude proposals whose author count exceeds
        # max_authors. A single PEC with 200+ signatories creates O(n²) pairs
        # and drives edge density above 85%, making community detection invalid.
        coauthorships = coauthorships[coauthorships.apply(len) <= max_authors]

        return deputy_map, groups, coauthorships, type_map

    def process_raw_data_unfiltered(
        self,
        raw_df: pd.DataFrame,
        propositions_df: pd.DataFrame,
    ):
        """No-filter baseline of :meth:`process_raw_data` for sensitivity studies.

        Builds the co-authorship structures WITHOUT the proposition-type filter and
        WITHOUT the ``max_authors`` mass-signature filter, so their effect can be
        quantified (e.g. edge density climbing towards ~85% once mass-signature
        PECs are included). Returns the same 4-tuple as :meth:`process_raw_data`
        (``deputy_map, groups, coauthorships, type_map``), so its output feeds
        :meth:`convert_to_domain_objects` unchanged.

        NOTE: this method is NOT used by the current pipeline. It is kept as a
        ready-to-use baseline for a future sensitivity analysis of the filters;
        wire it into the pipeline only when that study is actually run.

        Returns:
            Tuple of (deputy_map, groups, coauthorships, type_map).
        """
        df_authors = raw_df.copy()
        df_props = propositions_df.copy()
        df_authors.columns = [c.strip().lower() for c in df_authors.columns]
        df_props.columns = [c.strip().lower() for c in df_props.columns]

        # No type filter: all proposition types are kept. The merge only attaches
        # each proposition's type so the domain objects remain well-formed.
        df_merged = df_authors.merge(
            df_props[['id', 'siglatipo']],
            left_on='idproposicao',
            right_on='id',
            how='inner',
        )
        type_map = df_merged.drop_duplicates('idproposicao').set_index('idproposicao')['siglatipo'].to_dict()

        df_deputies = df_merged[df_merged['codtipoautor'] == 10000].copy()
        df_deputies = df_deputies.dropna(subset=['iddeputadoautor'])
        df_deputies['iddeputadoautor'] = df_deputies['iddeputadoautor'].astype(int)

        df_meta = df_deputies.drop_duplicates(subset=['iddeputadoautor'], keep='last')
        deputy_map = df_meta.set_index('iddeputadoautor')[['nomeautor', 'siglapartidoautor', 'siglaufautor']].to_dict('index')

        groups = df_deputies.groupby('idproposicao')['iddeputadoautor'].apply(list)
        coauthorships = groups[groups.apply(len) > 1]
        # No max_authors filter here — omitting it is exactly the point of this baseline.

        return deputy_map, groups, coauthorships, type_map

    def convert_to_domain_objects(
        self,
        deputy_map: dict,
        groups: pd.Series,
        coauthorships: pd.Series,
        type_map: dict,
        year: int,
    ) -> tuple:
        """Convert raw data maps to domain objects.

        Args:
            deputy_map: Mapping of deputy_id -> metadata.
            groups: Grouping of deputies by proposition ID.
            coauthorships: Filtered groups with 2+ authors.
            type_map: Mapping of proposition_id -> proposition_type.
            year: Analysis year.

        Returns:
            Tuple of (deputies_dict, propositions_list, coauthorships_list).
        """
        # 1. Create Deputy objects (nodes)
        # Sanitize NaN/empty party and state codes — the Chamber API returns
        # blanks for deputies in transition between parties, on leave, or
        # suspended. We replace these with explicit sentinels so the dataset
        # remains coherent (no NaNs propagated to CSV/GEXF exports).
        deputies_dict = {}
        for deputy_id, info in deputy_map.items():
            party = info.get('siglapartidoautor')
            state = info.get('siglaufautor')
            party_code = str(party).strip() if pd.notna(party) and str(party).strip() else "S/PARTIDO"
            state_code = str(state).strip() if pd.notna(state) and str(state).strip() else "S/UF"
            deputies_dict[deputy_id] = Deputy(
                id=deputy_id,
                name=info['nomeautor'],
                party_code=party_code,
                state_code=state_code,
            )

        # 2. Co-authorship propositions only (edges subset)
        coauthorships_list = []
        for prop_id, author_ids in coauthorships.items():
            coauthorships_list.append(Proposition(
                id=prop_id,
                year=year,
                author_ids=author_ids,
                proposition_type=type_map.get(prop_id, "N/A"),
            ))

        # 3. All propositions (individual + collective)
        propositions_list = []
        for prop_id, author_ids in groups.items():
            propositions_list.append(Proposition(
                id=prop_id,
                year=year,
                author_ids=author_ids,
                proposition_type=type_map.get(prop_id, "N/A"),
            ))

        return deputies_dict, propositions_list, coauthorships_list
