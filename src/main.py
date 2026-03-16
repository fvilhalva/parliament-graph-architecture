import os
import pandas as pd # type: ignore
from itertools import islice
from dotenv import load_dotenv  # type: ignore

from config import Config, setup_logger
from extraction import CamaraExtractor
from processing import CamaraProcessor
from core import CamaraGraph
from repository import CsvRepository, GraphExporter, DB_Exporter

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
    return df_bruto, df_meta, df


def etapa_processing(df_bruto, df_meta, ano):
    """2️⃣ Limpeza e conversão para objetos"""
    logger.info("Processamento de dados...")
    processor = CamaraProcessor()
    
    # 1. Limpeza e extração das coautorias (Pandas)
    mapa_deputados, grupos, coautorias, mapa_tipos = processor.processar_dados_brutos(df_bruto, df_meta)
    
    # 2. Conversão para as dataclasses
    dict_deputados, lista_proposicoes, lista_coautorias = processor.converter_para_modelos(mapa_deputados, grupos, coautorias, mapa_tipos, ano)
    
    # Retorne tudo o que for necessário para as próximas etapas
    return dict_deputados, lista_proposicoes, lista_coautorias, processor

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


def etapa_repository(grafo, deputados, ano):
    """5️⃣ Exportação para GEXF, CSV e SQLite"""
    logger.info("Exportando dados...")

    graph_exporter = GraphExporter(Config.GEXF_DIR)
    gexf_file = graph_exporter.exportar_gexf(grafo, ano=ano)
    logger.info(f"GEXF exportado em: {gexf_file}")

    csv_repository = CsvRepository(Config.METRICAS_DIR)
    output_file = csv_repository.exportar_metricas_deputados(deputados, ano)
    logger.info(f"CSV de métricas exportado em: {output_file}")

    db_repository = DB_Exporter(Config.DB_PATH)
    db_path = db_repository.exportar_metricas_deputados(deputados, ano)
    logger.info(f"SQLite exportado em: {db_path}")

def etapa_visualization(grafo, deputados):
    """6️⃣ Geração de visualizações"""
    logger.info("Gerando visualizações...")
    pass

def run_pipeline(ano: int):
    """Pipeline principal"""
    logger.info("=== INICIANDO PIPELINE DE ANÁLISE PARLAMENTAR ===")
    
    try:
        # 1. Extraction df_bruto
        # _camaraExtrator é uma instancia de CamaraExtrator(Classe)
        df_bruto, df_meta, _camaraExtrator = etapa_extraction(ano)
        # 2. Processin
        # _camaraProcessor é uma instancia de CamaraProcessor(Classe)
        dict_deputados, lista_proposicoes, lista_coautorias, _camaraProcessor = etapa_processing(df_bruto, df_meta, ano)
        print(f"Quantidade de deputados: {len(dict_deputados)}")
        print(f"Quantidade de proposicoes(): {len(lista_proposicoes)}")
        print(f"Quantidade de coautorias(entre 2 ou mais deputados): {len(lista_coautorias)}")
        print("COAUTORIAS: ")
        print(lista_coautorias)

        # 3. Core
        # grafo ja é uma instancia de CamaraGraph
        grafo = etapa_core(dict_deputados, lista_proposicoes, lista_coautorias, ano)
        deputados_centralidade = grafo.filtro_centralidade() # alterar para alterar na instacia
        grafo.filtro_intermediacao()
        grafo.exibir_perfil_deputado("nikolas ferreira")
        grafo.analise_estrutural_avancada()
        
        # 4. Algorithms
        #etapa_algorithms(grafo, deputados)
        # 5. Repository
        # etapa_repository(grafo, deputados_centralidade, ano)
        # 6. Visualization
        #etapa_visualization(grafo, deputados)
        
        logger.info("✅ PIPELINE CONCLUÍDO COM SUCESSO!")
    except Exception as e:
        logger.error(f"❌ Erro no pipeline: {e}")
        raise

if __name__ == "__main__":
    run_pipeline(2025)