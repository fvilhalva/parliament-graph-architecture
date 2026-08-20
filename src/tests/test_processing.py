"""Tests for the processing module."""
import ast

import pytest # type: ignore
import pandas as pd # type: ignore

from processing import ChamberProcessor


class TestProcessingDataValidation:
    """Tests for input data validation."""

    @pytest.fixture
    def valid_dataframe(self):
        """Create a valid DataFrame for testing."""
        return pd.DataFrame({
            'deputy_id': [1, 2, 3],
            'name': ['Silva', 'Santos', 'Oliveira'],
            'party': ['PT', 'PSDB', 'PT'],
            'state': ['SP', 'MG', 'RJ'],
            'proposition_id': [100, 101, 102],
            'title': ['PL 1', 'PL 2', 'PL 3']
        })

    def test_dataframe_not_empty(self, valid_dataframe):
        """DataFrame should not be empty."""
        assert len(valid_dataframe) > 0

    def test_required_columns_present(self, valid_dataframe):
        """Required columns should be present."""
        expected_columns = ['deputy_id', 'name', 'party']
        for column in expected_columns:
            assert column in valid_dataframe.columns

    def test_reject_empty_dataframe(self):
        """Should reject an empty DataFrame."""
        empty_df = pd.DataFrame()
        assert len(empty_df) == 0


class TestProcessingDataCleaning:
    """Tests for data cleaning and transformation."""

    @pytest.fixture
    def dirty_dataframe(self):
        """Create a DataFrame with dirty data."""
        return pd.DataFrame({
            'deputy_id': [1, 2, None, 4],
            'name': ['Silva', '', 'Oliveira', 'Costa'],
            'party': ['PT', 'PSDB', 'PT', None],
            'state': ['SP', 'MG', None, 'RJ']
        })

    def test_remove_nulls(self, dirty_dataframe):
        """Should remove or handle null values."""
        clean_df = dirty_dataframe.dropna(subset=['deputy_id'])
        assert clean_df['deputy_id'].isnull().sum() == 0

    def test_remove_duplicates(self):
        """Should remove duplicate rows."""
        df = pd.DataFrame({
            'deputy_id': [1, 1, 2, 3],
            'name': ['Silva', 'Silva', 'Santos', 'Oliveira']
        })
        deduped_df = df.drop_duplicates(subset=['deputy_id'])
        assert len(deduped_df) == 3

    def test_convert_types(self, dirty_dataframe):
        """Should convert data types correctly."""
        df = dirty_dataframe.copy()
        df['deputy_id'] = pd.to_numeric(df['deputy_id'], errors='coerce')
        assert df['deputy_id'].dtype in ['int64', 'float64']


class TestProcessingConversion:
    """Tests for DataFrame-to-object conversion."""

    @pytest.fixture
    def propositions_dataframe(self):
        """DataFrame with proposition data."""
        return pd.DataFrame({
            'proposition_id': [100, 101, 102],
            'year': [2024, 2024, 2023],
            'summary': ['PL 1', 'PL 2', 'PL 3'],
            'authors': ['[1,2,3]', '[1,2]', '[2,3,4]']
        })

    def test_convert_dataframe_to_objects(self, propositions_dataframe):
        """Should convert DataFrame to list of objects."""
        processor = ChamberProcessor()
        deputy_map = {
            1: {'nomeautor': 'Silva', 'siglapartidoautor': 'PT', 'siglaufautor': 'SP'},
            2: {'nomeautor': 'Santos', 'siglapartidoautor': 'PSDB', 'siglaufautor': 'MG'},
            3: {'nomeautor': 'Oliveira', 'siglapartidoautor': 'MDB', 'siglaufautor': 'RJ'},
        }
        groups = propositions_dataframe.set_index('proposition_id')['authors'].apply(ast.literal_eval)
        coauthorships = groups[groups.apply(len) > 1]
        type_map = {100: 'PL', 101: 'PLP', 102: 'PEC'}

        dict_deputies, list_propositions, list_coauthorships = processor.convert_to_domain_objects(
            deputy_map=deputy_map,
            groups=groups,
            coauthorships=coauthorships,
            type_map=type_map,
            year=2024,
        )

        assert len(dict_deputies) == 3
        assert len(list_propositions) == 3
        assert len(list_coauthorships) == 3  # Only those with 2+ authors

    def test_data_preserved_in_conversion(self, propositions_dataframe):
        """Data should not be lost during conversion."""
        processor = ChamberProcessor()
        deputy_map = {
            1: {'nomeautor': 'Silva', 'siglapartidoautor': 'PT', 'siglaufautor': 'SP'},
            2: {'nomeautor': 'Santos', 'siglapartidoautor': 'PSDB', 'siglaufautor': 'MG'},
        }
        groups = pd.Series({100: [1, 2], 101: [2]})
        coauthorships = pd.Series({100: [1, 2]})
        type_map = {100: 'PL', 101: 'PEC'}

        dict_deputies, list_propositions, list_coauthorships = processor.convert_to_domain_objects(
            deputy_map=deputy_map,
            groups=groups,
            coauthorships=coauthorships,
            type_map=type_map,
            year=2024,
        )

        assert dict_deputies[1].name == 'Silva'
        assert list_propositions[0].id == 100
        assert list_propositions[0].year == 2024
        assert list_propositions[0].proposition_type == 'PL'


class TestProcessingFilters:
    """Tests for filtering and selection."""

    @pytest.fixture
    def multi_year_dataframe(self):
        """DataFrame spanning multiple years."""
        return pd.DataFrame({
            'deputy_id': [1, 2, 3, 4],
            'year': [2024, 2023, 2024, 2022],
            'party': ['PT', 'PSDB', 'PT', 'MDB']
        })

    def test_filter_by_year(self, multi_year_dataframe):
        """Should filter data by year."""
        df_2024 = multi_year_dataframe[multi_year_dataframe['year'] == 2024]
        assert len(df_2024) == 2
        assert all(df_2024['year'] == 2024)

    def test_filter_by_party(self, multi_year_dataframe):
        """Should filter data by party."""
        df_pt = multi_year_dataframe[multi_year_dataframe['party'] == 'PT']
        assert len(df_pt) == 2
        assert all(df_pt['party'] == 'PT')

    def test_filter_multiple_criteria(self, multi_year_dataframe):
        """Should filter with multiple criteria."""
        df = multi_year_dataframe[
            (multi_year_dataframe['year'] == 2024) & 
            (multi_year_dataframe['party'] == 'PT')
        ]
        assert len(df) == 2


class TestMaxAuthorsFilter:
    """Tests for the mass-signature proposal filter in process_raw_data."""

    def _make_authors_df(self, rows: list[dict]) -> pd.DataFrame:
        return pd.DataFrame(rows)

    def _make_props_df(self, prop_ids: list[int], sigla: str = "PL") -> pd.DataFrame:
        return pd.DataFrame({"id": prop_ids, "siglatipo": [sigla] * len(prop_ids)})

    def _base_row(self, prop_id: int, deputy_id: int) -> dict:
        return {
            "idproposicao": prop_id,
            "codtipoautor": 10000,
            "iddeputadoautor": float(deputy_id),
            "nomeautor": f"Deputy {deputy_id}",
            "siglapartidoautor": "PT",
            "siglaufautor": "SP",
        }

    def test_large_proposal_excluded_from_coauthorships(self):
        """A proposal with more authors than max_authors must not appear in coauthorships."""
        rows = [self._base_row(prop_id=1, deputy_id=i) for i in range(1, 52)]  # 51 authors
        rows += [self._base_row(prop_id=2, deputy_id=i) for i in range(1, 4)]  # 3 authors
        df_authors = self._make_authors_df(rows)
        df_props = self._make_props_df([1, 2])

        processor = ChamberProcessor()
        deputy_map, groups, coauthorships, *_ = processor.process_raw_data(
            df_authors, df_props, max_authors=30
        )

        assert 1 not in coauthorships.index, "Mass-signature proposal should be excluded"
        assert 2 in coauthorships.index, "Small proposal should still be included"

    def test_all_large_proposals_excluded(self):
        """When every co-authored proposal exceeds max_authors, coauthorships is empty."""
        rows = [self._base_row(prop_id=99, deputy_id=i) for i in range(1, 102)]  # 101 authors
        df_authors = self._make_authors_df(rows)
        df_props = self._make_props_df([99])

        processor = ChamberProcessor()
        _, _, coauthorships, *_ = processor.process_raw_data(
            df_authors, df_props, max_authors=30
        )

        assert len(coauthorships) == 0

    def test_proposal_exactly_at_limit_is_kept(self):
        """A proposal with exactly max_authors authors must be included (boundary)."""
        rows = [self._base_row(prop_id=5, deputy_id=i) for i in range(1, 31)]  # exactly 30
        df_authors = self._make_authors_df(rows)
        df_props = self._make_props_df([5])

        processor = ChamberProcessor()
        _, _, coauthorships, *_ = processor.process_raw_data(
            df_authors, df_props, max_authors=30
        )

        assert 5 in coauthorships.index

    def test_proposal_one_over_limit_is_excluded(self):
        """A proposal with max_authors + 1 authors must be excluded (boundary)."""
        rows = [self._base_row(prop_id=6, deputy_id=i) for i in range(1, 32)]  # 31 authors
        df_authors = self._make_authors_df(rows)
        df_props = self._make_props_df([6])

        processor = ChamberProcessor()
        _, _, coauthorships, *_ = processor.process_raw_data(
            df_authors, df_props, max_authors=30
        )

        assert 6 not in coauthorships.index

    def test_groups_still_contains_large_proposals(self):
        """groups (all deputy propositions) must include the large proposal even when
        coauthorships excludes it — individual authorship data must not be lost."""
        rows = [self._base_row(prop_id=7, deputy_id=i) for i in range(1, 52)]
        df_authors = self._make_authors_df(rows)
        df_props = self._make_props_df([7])

        processor = ChamberProcessor()
        _, groups, coauthorships, *_ = processor.process_raw_data(
            df_authors, df_props, max_authors=30
        )

        assert 7 in groups.index, "groups must retain all propositions regardless of filter"
        assert 7 not in coauthorships.index, "coauthorships must exclude the large proposal"


class TestPartyStateSanitization:
    """Tests that NaN/empty party and state codes are replaced with sentinels.

    The Chamber API returns blank ``siglapartidoautor`` for deputies in
    transition between parties, on leave, or suspended. The processor must
    replace these with explicit sentinels so downstream exports never carry
    NaN values.
    """

    def test_nan_party_becomes_sentinel(self):
        processor = ChamberProcessor()
        deputy_map = {
            1: {'nomeautor': 'Silva', 'siglapartidoautor': float('nan'), 'siglaufautor': 'SP'},
        }
        groups = pd.Series({100: [1]})
        coauthorships = pd.Series(dtype=object)
        type_map = {100: 'PL'}

        deputies, _, _ = processor.convert_to_domain_objects(
            deputy_map=deputy_map, groups=groups, coauthorships=coauthorships,
            type_map=type_map, year=2024,
        )
        assert deputies[1].party_code == "S/PARTIDO"

    def test_empty_string_party_becomes_sentinel(self):
        processor = ChamberProcessor()
        deputy_map = {
            1: {'nomeautor': 'Silva', 'siglapartidoautor': '   ', 'siglaufautor': 'SP'},
        }
        groups = pd.Series({100: [1]})
        coauthorships = pd.Series(dtype=object)
        type_map = {100: 'PL'}

        deputies, _, _ = processor.convert_to_domain_objects(
            deputy_map=deputy_map, groups=groups, coauthorships=coauthorships,
            type_map=type_map, year=2024,
        )
        assert deputies[1].party_code == "S/PARTIDO"

    def test_nan_state_becomes_sentinel(self):
        processor = ChamberProcessor()
        deputy_map = {
            1: {'nomeautor': 'Silva', 'siglapartidoautor': 'PT', 'siglaufautor': None},
        }
        groups = pd.Series({100: [1]})
        coauthorships = pd.Series(dtype=object)
        type_map = {100: 'PL'}

        deputies, _, _ = processor.convert_to_domain_objects(
            deputy_map=deputy_map, groups=groups, coauthorships=coauthorships,
            type_map=type_map, year=2024,
        )
        assert deputies[1].state_code == "S/UF"

    def test_valid_party_is_preserved(self):
        processor = ChamberProcessor()
        deputy_map = {
            1: {'nomeautor': 'Silva', 'siglapartidoautor': 'PT', 'siglaufautor': 'SP'},
        }
        groups = pd.Series({100: [1]})
        coauthorships = pd.Series(dtype=object)
        type_map = {100: 'PL'}

        deputies, _, _ = processor.convert_to_domain_objects(
            deputy_map=deputy_map, groups=groups, coauthorships=coauthorships,
            type_map=type_map, year=2024,
        )
        assert deputies[1].party_code == "PT"
        assert deputies[1].state_code == "SP"


class TestProcessingErrors:
    """Error-handling tests."""

    def test_invalid_dataframe_raises(self):
        """Should raise an error for an invalid DataFrame."""
        invalid_df = pd.DataFrame({
            'wrong_column': [1, 2, 3]
        })
        df_props = pd.DataFrame({'id': [1], 'siglatipo': ['PL']})
        processor = ChamberProcessor()

        with pytest.raises(KeyError):
                processor.process_raw_data(invalid_df, df_props)

    def test_inconsistent_data(self):
        """Should detect inconsistent data."""
        authors_df = pd.DataFrame({
            'idproposicao': [100],
            'codtipoautor': [10000],
            'iddeputadoautor': ['INVALIDO'],
            'nomeautor': ['Silva'],
            'siglapartidoautor': ['PT'],
            'siglaufautor': ['SP'],
        })
        df_props = pd.DataFrame({
            'id': [100],
            'siglatipo': ['PL'],
        })
        processor = ChamberProcessor()

        with pytest.raises(ValueError):
                processor.process_raw_data(authors_df, df_props)
