import requests
import sqlite3
import os
from dotenv import load_dotenv

# 1. Carrega as definições do seu .env
load_dotenv()

# 2. Atribui às variáveis (o segundo argumento é o "fallback" caso o .env suma)
LEGISLATURA = os.getenv('LEGISLATURA_ATUAL', '57')
DB_PATH = os.getenv('DB_PATH', 'data/camara_padrao.db')
BASE_URL = os.getenv('API_BASE_URL', 'https://dadosabertos.camara.leg.br/api/v2')

# 3. Configura o Banco de Dados
# Isso garante que se o DB_PATH for 'data/algo.db', a pasta 'data' exista
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def inicializar_banco():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deputados (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            siglaPartido TEXT,
            siglaUf TEXT
        )
    ''')
    conn.commit()

def extrair_deputados():
    print(f"📡 Conectando em: {BASE_URL}")
    print(f"🔎 Buscando deputados da {LEGISLATURA}ª legislatura...")
    
    # Monta a URL usando as variáveis do seu .env
    url = f"{BASE_URL}/deputados?idLegislatura={LEGISLATURA}"
    
    try:
        resposta = requests.get(url)
        resposta.raise_for_status() # Gera erro se a API cair (404, 500, etc)
        
        dados = resposta.json()['dados']
        for dep in dados:
            cursor.execute('''
                INSERT OR IGNORE INTO deputados (id, nome, siglaPartido, siglaUf)
                VALUES (?, ?, ?, ?)
            ''', (dep['id'], dep['nome'], dep['siglaPartido'], dep['siglaUf']))
            
        conn.commit()
        print(f"🚀 Sucesso! {len(dados)} deputados salvos em {DB_PATH}")
        
    except Exception as e:
        print(f"❌ Falha na extração: {e}")

if __name__ == "__main__":
    inicializar_banco()
    extrair_deputados()
    conn.close()