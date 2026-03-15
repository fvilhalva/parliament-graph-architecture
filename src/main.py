import os
import pandas as pd # type: ignore
from itertools import islice
from dotenv import load_dotenv  # type: ignore

from config import Config, setup_logger
from extraction import CamaraExtractor
from processing import CamaraProcessor
from core import CamaraGraph

logger = setup_logger(__name__)
config = Config()
print(Config.DATA_DIR)

# Carrega variáveis de ambiente
load_dotenv()
LEGISLATURA_INICIO = config.LEGISLATURA_INICIO
LEGISLATURA_ATUAL = config.LEGISLATURA_ATUAL
LEGISLATURA_ITERATOR = LEGISLATURA_ATUAL #LEGISLATURA_INICIO
DB_PATH = config.DB_PATH
API_BASE_URL = config.API_BASE_URL

def etapa_extraction(ano) -> pd.DataFrame:
    """1️⃣ Extração de dados brutos"""
    logger.info("Extração de dados...")
    df = CamaraExtractor(config)
    df_bruto = df.extrair_dados_brutos(ano) # extrai as proposicoes
    df_meta = df.extrair_metadados_proposicoes(ano) # extrai as proposicoes
    return df_bruto, df_meta


def etapa_processing(df_bruto, df_meta, filtro, ano):
    """2️⃣ Limpeza e conversão para objetos"""
    logger.info("Processamento de dados...")
    processor = CamaraProcessor()
    
    # 1. Limpeza e extração das coautorias (Pandas)
    mapa_deputados, grupos, coautorias, mapa_tipos = processor.processar_dados_brutos(df_bruto, df_meta, filtro)
    
    # 2. Conversão para as dataclasses
    dict_deputados, lista_proposicoes, lista_coautorias = processor.converter_para_modelos(mapa_deputados, grupos, coautorias, mapa_tipos, ano)
    
    # Retorne tudo o que for necessário para as próximas etapas
    return dict_deputados, lista_proposicoes, lista_coautorias

def etapa_core(deputados, proposicoes, coautorias, ano):
    """3️⃣ Construção do grafo"""
    logger.info("Construindo grafo...")
    grafo = CamaraGraph(deputados, proposicoes, coautorias, ano)
    grafo.construir_grafo()
    return grafo


def etapa_algorithms(grafo, deputados):
    """4️⃣ Cálculo de métricas e detecção de comunidades"""
    logger.info("Calculando métricas...")
    pass


def etapa_repository(grafo, deputados, proposicoes, arestas):
    """5️⃣ Exportação para GEXF, CSV e SQLite"""
    logger.info("Exportando dados...")
    pass


def etapa_visualization(grafo, deputados):
    """6️⃣ Geração de visualizações"""
    logger.info("Gerando visualizações...")
    pass

def run_pipeline(ano: int):
    """Pipeline principal"""
    logger.info("=== INICIANDO PIPELINE DE ANÁLISE PARLAMENTAR ===")
    
    try:
        # 1. Extraction df_bruto
        df_bruto, df_meta = etapa_extraction(ano)
        # 2. Processing
        filtro =  ['PL', 'PEC', 'PLP']
        dict_deputados, lista_proposicoes, lista_coautorias = etapa_processing(df_bruto, df_meta, filtro, ano)
        print(f"Quantidade de deputados: {len(dict_deputados)}")
        print(f"Quantidade de proposicoes({filtro}): {len(lista_proposicoes)}")
        print(f"Quantidade de coautorias(entre 2 ou mais deputados): {len(lista_coautorias)}")
        print("COAUTORIAS: ")
        #print(lista_coautorias)

        # 3. Core
        grafo = etapa_core(dict_deputados, lista_proposicoes, lista_coautorias, ano)
        print(grafo.filtro_centralidade())
        print(grafo.filtro_intermediacao())
        grafo.exibir_perfil_deputado("nikolas ferreira")
        grafo.analise_estrutural_avancada()
        
        # 4. Algorithms
        #etapa_algorithms(grafo, deputados)
        # 5. Repository
        #etapa_repository(grafo, deputados, proposicoes, arestas)
        # 6. Visualization
        #etapa_visualization(grafo, deputados)
        
        logger.info("✅ PIPELINE CONCLUÍDO COM SUCESSO!")
    except Exception as e:
        logger.error(f"❌ Erro no pipeline: {e}")
        raise

if __name__ == "__main__":
    run_pipeline(2025)