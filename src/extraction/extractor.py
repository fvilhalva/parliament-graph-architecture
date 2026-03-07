# extraction/client.py
import requests # type: ignore

class CamaraExtractor:
    def __init__(self, api_url, legislatura):
        self.api_url = api_url
        self.legislatura = legislatura

    def search_deputados(self, limite=20):
        url = f"{self.api_url}/deputados?idLegislatura={self.legislatura}&itens={limite}"
        try:
            resposta = requests.get(url)
            resposta.raise_for_status()
            return resposta.json().get('dados', [])
        except Exception as e:
            print(f"Erro ao buscar: {e}")
            return []
    
    def search_proposicoes(self, limite=20):
        ...