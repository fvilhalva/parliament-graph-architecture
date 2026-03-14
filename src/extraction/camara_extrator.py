import pandas as pd  # type: ignore
import requests  # type: ignore
import zipfile
import shutil
from pathlib import Path
from config import Config


class CamaraExtractor:
    def __init__(self, config: Config):
        self.config = config
        self.cache_dir = config.DATA_DIR / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def extrair_dados_brutos(self, ano: int) -> pd.DataFrame:
        """Extrai dados brutos de autores de proposições, usando cache local"""
        url = self.config.get_url_csv(ano)
        arquivo = self._baixar_e_descompactar(url, ano, "proposicoesAutores")
        df_bruto = pd.read_csv(arquivo, sep=";")
        return df_bruto

    def extrair_metadados_proposicoes(self, ano: int) -> pd.DataFrame:
        """Extrai o CSV de Proposições (onde está a siglaTipo e Ementa)"""
        url = self.config.get_url_csv_proposicoes(ano)
        arquivo = self._baixar_e_descompactar(url, ano, "proposicoes")
        df_meta = pd.read_csv(arquivo, sep=";")
        return df_meta

    def _baixar_e_descompactar(self, url: str, ano: int, tipo: str) -> Path:
        """
        Baixa arquivo pela URL, salva em cache e descompacta se necessário.
        
        Args:
            url: URL do arquivo
            ano: Ano para identificar o arquivo em cache
            tipo: Tipo de dados (proposicoesAutores, proposicoes, etc)
            
        Returns:
            Path: Caminho para o arquivo CSV descompactado
        """
        # Definir caminhos
        arquivo_zip = self.cache_dir / f"{tipo}-{ano}.zip"
        arquivo_csv_direto = self.cache_dir / f"{tipo}-{ano}.csv"
        pasta_descompactada = self.cache_dir / f"{tipo}-{ano}"
        arquivo_csv_em_pasta = pasta_descompactada / f"{tipo}-{ano}.csv"
        
        # Se o CSV já existe (descompactado ou direto), retornar
        if arquivo_csv_em_pasta.exists():
            print(f"✓ Usando cache: {arquivo_csv_em_pasta}")
            return arquivo_csv_em_pasta
        if arquivo_csv_direto.exists():
            print(f"✓ Usando cache: {arquivo_csv_direto}")
            return arquivo_csv_direto
        
        # Se o ZIP não existe, baixar
        if not arquivo_zip.exists():
            print(f"⬇ Baixando {tipo} para {ano}...")
            self._baixar_arquivo(url, arquivo_zip)
        
        # Verificar se é realmente um ZIP
        if not zipfile.is_zipfile(arquivo_zip):
            print(f"ℹ  Arquivo é CSV direto (não compactado), movendo para cache...")
            shutil.move(str(arquivo_zip), str(arquivo_csv_direto))
            print(f"✓ CSV salvo em: {arquivo_csv_direto}")
            return arquivo_csv_direto
        
        # Descompactar
        print(f"📦 Descompactando {arquivo_zip.name}...")
        pasta_descompactada.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
            zip_ref.extractall(pasta_descompactada)
        
        print(f"✓ Descompactado em {pasta_descompactada}")
        return arquivo_csv_em_pasta

    def _baixar_arquivo(self, url: str, caminho_destino: Path):
        """
        Baixa arquivo da URL e salva no caminho especificado.
        
        Args:
            url: URL do arquivo
            caminho_destino: Path onde salvar o arquivo
        """
        try:
            response = requests.get(url, timeout=self.config.API_TIMEOUT, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(caminho_destino, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percentual = (downloaded / total_size) * 100
                            print(f"  {percentual:.1f}%", end="\r")
            
            print(f"\n✓ Arquivo salvo: {caminho_destino}")
        except requests.exceptions.RequestException as e:
            print(f"✗ Erro ao baixar {url}: {e}")
            raise

    def _fazer_requisicao(self, url: str, params: dict) -> dict:
        # Wrapper com retry, timeout, tratamento de erro
        # Rate limit respeitoso
        pass

    def _cachear(self, chave: str, dados: pd.DataFrame):
        # Salva em CSV/pickle para não refazer requisição
        pass
