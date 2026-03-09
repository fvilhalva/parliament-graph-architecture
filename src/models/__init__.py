# extraction/__init__.py
from .deputado  import Deputado
from .proposicao import Proposicao
from .aresta_coautoria import ArestaCoautoria
from .rede_parlamentar import RedeParlamentar

__all__ = [
           'Deputado',
           'Proposicao',
           'ArestaCoautoria',
           'RedeParlamentar'
        ]