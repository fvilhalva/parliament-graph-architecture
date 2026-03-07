# Usa uma imagem oficial do Python, versão enxuta
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema operacional necessárias para compilar pacotes C/C++ 
# (Algumas bibliotecas de Ciência de Dados precisam disso)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requisitos primeiro (para aproveitar o cache do Docker)
COPY requirements.txt .

# Instala as bibliotecas Python (Pandas, NetworkX, Scikit-learn, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do código fonte para dentro do container
COPY . .

# Cria a pasta onde o SQLite e os arquivos do Gephi (.gexf) serão salvos
RUN mkdir -p /app/data

# Comando padrão ao iniciar o container (pode ser o seu orquestrador do pipeline)
CMD ["python", "src/main.py"]