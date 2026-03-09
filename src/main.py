import os
import json
from dotenv import load_dotenv # type: ignore
from extraction import CamaraExtractor

# Carrega o arquivo .env
load_dotenv()

# Acessa as variáveis
LEGISLATURA_ATUAL = os.getenv("LEGISLATURA_ATUAL")
DB_PATH = os.getenv("DB_PATH")
API_BASE_URL = os.getenv("API_BASE_URL")

if __name__ == "__main__":
    extractor = CamaraExtractor()
    print(extractor.teste())