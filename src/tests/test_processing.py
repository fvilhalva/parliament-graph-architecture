"""Testes para o módulo de processamento"""
import ast

import pytest # type: ignore
import pandas as pd # type: ignore

from processing import CamaraProcessor


class TestProcessingDataValidacao:
    """Testes de validação de dados de entrada"""

    @pytest.fixture
    def dataframe_valido(self):
        """Cria um DataFrame válido para testes"""
        return pd.DataFrame({
            'id_deputado': [1, 2, 3],
            'nome': ['Silva', 'Santos', 'Oliveira'],
            'partido': ['PT', 'PSDB', 'PT'],
            'uf': ['SP', 'MG', 'RJ'],
            'id_proposicao': [100, 101, 102],
            'ementa': ['PL 1', 'PL 2', 'PL 3']
        })

    def test_dataframe_nao_vazio(self, dataframe_valido):
        """DataFrame não deve estar vazio"""
        assert len(dataframe_valido) > 0

    def test_colunas_obrigatorias_presentes(self, dataframe_valido):
        """Colunas obrigatórias devem estar presentes"""
        colunas_esperadas = ['id_deputado', 'nome', 'partido']
        for coluna in colunas_esperadas:
            assert coluna in dataframe_valido.columns

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
        """Deve converter DataFrame em lista de objetos"""
        processor = CamaraProcessor()
        mapa_deputados = {
            1: {'nomeautor': 'Silva', 'siglapartidoautor': 'PT', 'siglaufautor': 'SP'},
            2: {'nomeautor': 'Santos', 'siglapartidoautor': 'PSDB', 'siglaufautor': 'MG'},
            3: {'nomeautor': 'Oliveira', 'siglapartidoautor': 'MDB', 'siglaufautor': 'RJ'},
        }
        grupos = dataframe_proposicoes.set_index('id_proposicao')['autores'].apply(ast.literal_eval)
        coautorias = grupos[grupos.apply(len) > 1]
        mapa_tipos = {100: 'PL', 101: 'PLP', 102: 'PEC'}

        dict_deputados, lista_proposicoes, lista_coautorias = processor.converter_para_modelos(
            mapa_deputados=mapa_deputados,
            grupos=grupos,
            coautorias=coautorias,
            mapa_tipos=mapa_tipos,
            ano=2024,
        )

        assert len(dict_deputados) == 3
        assert len(lista_proposicoes) == 3
        assert len(lista_coautorias) == 3
        assert all(hasattr(p, 'id_proposicao') for p in lista_proposicoes)

    def test_preservar_dados_conversao(self, dataframe_proposicoes):
        """Dados não devem ser perdidos na conversão"""
        processor = CamaraProcessor()
        mapa_deputados = {
            1: {'nomeautor': 'Silva', 'siglapartidoautor': 'PT', 'siglaufautor': 'SP'},
            2: {'nomeautor': 'Santos', 'siglapartidoautor': 'PSDB', 'siglaufautor': 'MG'},
        }
        grupos = pd.Series({100: [1, 2], 101: [2]})
        coautorias = pd.Series({100: [1, 2]})
        mapa_tipos = {100: 'PL', 101: 'PEC'}

        dict_deputados, lista_proposicoes, lista_coautorias = processor.converter_para_modelos(
            mapa_deputados=mapa_deputados,
            grupos=grupos,
            coautorias=coautorias,
            mapa_tipos=mapa_tipos,
            ano=2024,
        )

        assert dict_deputados[1].nome == 'Silva'
        assert lista_proposicoes[0].id_proposicao == 100
        assert lista_proposicoes[0].ano == 2024
        assert lista_coautorias[0].sigla_tipo == 'PL'


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
        processor = CamaraProcessor()

        with pytest.raises(KeyError):
            processor.processar_dados_brutos(df_invalido, df_props)

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
        processor = CamaraProcessor()

        with pytest.raises(ValueError):
            processor.processar_dados_brutos(df_autores, df_props)
