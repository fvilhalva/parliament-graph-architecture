import os
import pandas as pd # type: ignore
from dotenv import load_dotenv  # type: ignore

from config import Config, setup_logger
from extraction import CamaraExtractor
from processing import CamaraProcessor

logger = setup_logger(__name__)
config = Config()
print(Config.DATA_DIR)

# Carrega variáveis de ambiente
load_dotenv()
LEGISLATURA_INICIO = config.LEGISLATURA_INICIO
LEGISLATURA_ATUAL = config.LEGISLATURA_ATUAL
LEGISLATURA_ITERATOR = LEGISLATURA_INICIO
DB_PATH = config.DB_PATH
API_BASE_URL = config.API_BASE_URL

def etapa_extraction(ano) -> pd.DataFrame:
    """1️⃣ Extração de dados brutos"""
    logger.info("Extração de dados...")
    return CamaraExtractor(config).extrair_dados_brutos(ano)


def etapa_processing(df_bruto):
    """2️⃣ Limpeza e conversão para objetos"""
    logger.info("Processamento de dados...")
    return CamaraProcessor().processar_coautorias(df_bruto)

def etapa_core(deputados, proposicoes, arestas):
    """3️⃣ Construção do grafo"""
    logger.info("Construindo grafo...")
    pass


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
        df_bruto = etapa_extraction(ano)
        # 2. Processing
        mapa_deputados, proposicoes, coautorias = etapa_processing(df_bruto)
        # 3. Core
        #grafo = etapa_core(deputados, proposicoes, arestas)
        
        # 4. Algorithms
        #etapa_algorithms(grafo, deputados)
        
        # 5. Repository
        #etapa_repository(grafo, deputados, proposicoes, arestas)
        
        # 6. Visualization
        #etapa_visualization(grafo, deputados)
        print("Hello Docker")
        
        logger.info("✅ PIPELINE CONCLUÍDO COM SUCESSO!")
    except Exception as e:
        logger.error(f"❌ Erro no pipeline: {e}")
        raise

if __name__ == "__main__":
    run_pipeline(LEGISLATURA_ITERATOR)