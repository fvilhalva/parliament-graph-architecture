import pandas as pd  # type: ignore
from pathlib import Path
from config import Config


class CamaraExtractor:
    def __init__(self, config: Config):
        self.config = config
        self.cache_dir = config.DATA_DIR / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def extrair_dados_brutos(self, ano: int) -> pd.DataFrame:
        """Extrai dados brutos de autores de proposicoes, usando cache local."""
        arquivo = self._obter_arquivo_local(ano, "proposicoesAutores")
        return pd.read_csv(arquivo, sep=";")

    def extrair_metadados_proposicoes(self, ano: int) -> pd.DataFrame:
        """Extrai o CSV de Proposicoes (onde estao siglaTipo e ementa)."""
        arquivo = self._obter_arquivo_local(ano, "proposicoes")
        return pd.read_csv(arquivo, sep=";")

    def _obter_arquivo_local(self, ano: int, tipo: str) -> Path:
        """Localiza CSV previamente baixado no diretorio data/ ou data/cache/."""
        nome = f"{tipo}-{ano}"
        candidatos = [
            self.config.DATA_DIR / f"{nome}.csv",
            self.cache_dir / f"{nome}.csv",
            self.cache_dir / f"{nome}.zip",
            self.cache_dir / nome / f"{nome}.csv",
        ]

        for caminho in candidatos:
            if caminho.exists() and self._csv_valido(caminho):
                print(f"✓ Usando arquivo local: {caminho}")
                return caminho

        raise FileNotFoundError(
            "Arquivo CSV nao encontrado ou invalido para "
            f"{tipo}/{ano}. Coloque um destes arquivos em data/ ou data/cache/: "
            + ", ".join(str(c.name) for c in candidatos)
        )

    def _csv_valido(self, caminho_csv: Path) -> bool:
        """Valida rapidamente se o arquivo CSV pode ser lido."""
        if not caminho_csv.exists() or caminho_csv.stat().st_size == 0:
            return False

        try:
            # Evita inferencia por extensao (.zip), pois a Camara pode servir CSV direto.
            pd.read_csv(caminho_csv, sep=";", nrows=5, compression=None)
            return True
        except Exception:
            return False

    def _fazer_requisicao(self, url: str, params: dict) -> dict:
        raise NotImplementedError("Metodo nao usado no modo offline.")

    def _cachear(self, chave: str, dados: pd.DataFrame):
        raise NotImplementedError("Metodo nao usado no modo offline.")
