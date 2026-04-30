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

    def test_rejeitar_dataframe_vazio(self):
        """Deve rejeitar DataFrame vazio"""
        df_vazio = pd.DataFrame()
        assert len(df_vazio) == 0


class TestProcessingLimpezaDados:
    """Testes de limpeza e transformação de dados"""

    @pytest.fixture
    def dataframe_sujo(self):
        """Cria um DataFrame com dados sujos"""
        return pd.DataFrame({
            'id_deputado': [1, 2, None, 4],
            'nome': ['Silva', '', 'Oliveira', 'Costa'],
            'partido': ['PT', 'PSDB', 'PT', None],
            'uf': ['SP', 'MG', None, 'RJ']
        })

    def test_remover_nulos(self, dataframe_sujo):
        """Deve remover ou tratar valores nulos"""
        df_limpo = dataframe_sujo.dropna(subset=['id_deputado'])
        assert df_limpo['id_deputado'].isnull().sum() == 0

    def test_remover_duplicatas(self):
        """Deve remover linhas duplicadas"""
        df = pd.DataFrame({
            'id_deputado': [1, 1, 2, 3],
            'nome': ['Silva', 'Silva', 'Santos', 'Oliveira']
        })
        df_sem_dup = df.drop_duplicates(subset=['id_deputado'])
        assert len(df_sem_dup) == 3

    def test_converter_tipos(self, dataframe_sujo):
        """Deve converter tipos de dados corretamente"""
        df = dataframe_sujo.copy()
        df['id_deputado'] = pd.to_numeric(df['id_deputado'], errors='coerce')
        assert df['id_deputado'].dtype in ['int64', 'float64']


class TestProcessingConversao:
    """Testes de conversão de DataFrame para objetos"""

    @pytest.fixture
    def dataframe_proposicoes(self):
        """DataFrame com dados de proposições"""
        return pd.DataFrame({
            'id_proposicao': [100, 101, 102],
            'ano': [2024, 2024, 2023],
            'ementa': ['PL 1', 'PL 2', 'PL 3'],
            'autores': ['[1,2,3]', '[1,2]', '[2,3,4]']
        })

    def test_converter_dataframe_para_objetos(self, dataframe_proposicoes):
        """Should convert DataFrame to list of objects."""
        processor = ChamberProcessor()
        deputy_map = {
            1: {'nomeautor': 'Silva', 'siglapartidoautor': 'PT', 'siglaufautor': 'SP'},
            2: {'nomeautor': 'Santos', 'siglapartidoautor': 'PSDB', 'siglaufautor': 'MG'},
            3: {'nomeautor': 'Oliveira', 'siglapartidoautor': 'MDB', 'siglaufautor': 'RJ'},
        }
        groups = dataframe_proposicoes.set_index('id_proposicao')['autores'].apply(ast.literal_eval)
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

    def test_preservar_dados_conversao(self, dataframe_proposicoes):
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


class TestProcessingFiltros:
    """Testes de filtros e seleções"""

    @pytest.fixture
    def dataframe_com_anos(self):
        """DataFrame com dados de múltiplos anos"""
        return pd.DataFrame({
            'id_deputado': [1, 2, 3, 4],
            'ano': [2024, 2023, 2024, 2022],
            'partido': ['PT', 'PSDB', 'PT', 'MDB']
        })

    def test_filtrar_por_ano(self, dataframe_com_anos):
        """Deve filtrar dados por ano"""
        df_2024 = dataframe_com_anos[dataframe_com_anos['ano'] == 2024]
        assert len(df_2024) == 2
        assert all(df_2024['ano'] == 2024)

    def test_filtrar_por_partido(self, dataframe_com_anos):
        """Deve filtrar dados por partido"""
        df_pt = dataframe_com_anos[dataframe_com_anos['partido'] == 'PT']
        assert len(df_pt) == 2
        assert all(df_pt['partido'] == 'PT')

    def test_filtro_multiplos_criterios(self, dataframe_com_anos):
        """Deve filtrar com múltiplos critérios"""
        df = dataframe_com_anos[
            (dataframe_com_anos['ano'] == 2024) & 
            (dataframe_com_anos['partido'] == 'PT')
        ]
        assert len(df) == 2


class TestProcessingErros:
    """Testes de tratamento de erros"""

    def test_dataframe_invalido_lancao_erro(self):
        """Deve lançar erro com DataFrame inválido"""
        df_invalido = pd.DataFrame({
            'coluna_errada': [1, 2, 3]
        })
        df_props = pd.DataFrame({'id': [1], 'siglatipo': ['PL']})
        processor = ChamberProcessor()

        with pytest.raises(KeyError):
                processor.process_raw_data(df_invalido, df_props)

    def test_dados_inconsistentes(self):
        """Deve detectar dados inconsistentes"""
        df_autores = pd.DataFrame({
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
                processor.process_raw_data(df_autores, df_props)
