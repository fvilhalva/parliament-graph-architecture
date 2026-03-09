import os
from dotenv import load_dotenv  # type: ignore

from config import Config, setup_logger
from extraction import CamaraExtractor

logger = setup_logger(__name__)
config = Config()
print(Config.DATA_DIR)

# Carrega variáveis de ambiente
load_dotenv()
LEGISLATURA_INICIO = config.LEGISLATURA_INICIO
LEGISLATURA_ATUAL = config.LEGISLATURA_ATUAL # = LEGISLATURA_INICIO  para iterar nos anos
DB_PATH = config.DB_PATH
API_BASE_URL = config.API_BASE_URL

def etapa_extraction():
    """1️⃣ Extração de dados brutos"""
    logger.info("Extração de dados...")
    return CamaraExtractor(config, LEGISLATURA_ATUAL).extrair_dados(LEGISLATURA_ATUAL)


def etapa_processing(df_bruto):
    """2️⃣ Limpeza e conversão para objetos"""
    logger.info("Processamento de dados...")
    pass


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


def main():
    """Pipeline principal"""
    logger.info("=== INICIANDO PIPELINE DE ANÁLISE PARLAMENTAR ===")
    
    try:
        # 1. Extraction df_bruto = 
        mapa_deputados, proposicoes, coautorias = etapa_extraction()

        print(f"Total de projetos com coautoria: {len(coautorias)}")
        print(f"Total de projetos: {len(proposicoes)}")
        print(f"Total de deputados: {len(mapa_deputados)}")
        
        # 2. Processing
        #deputados, proposicoes, arestas = etapa_processing(df_bruto)
        
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
    main()