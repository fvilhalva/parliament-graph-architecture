"""Contratos (interfaces) da camada de persistência.

Define, via ``typing.Protocol``, os *contratos* que a camada de repositório
oferece às camadas superiores. O pipeline (política de alto nível) passa a
depender destas abstrações --- e não das implementações concretas ---,
materializando o Princípio da Inversão de Dependência (DIP): trocar CSV por
outro formato tabular, ou SQLite por outro banco, não exige alterar o núcleo,
apenas fornecer outra implementação que satisfaça o mesmo contrato.

Os Protocols são estruturais: qualquer classe com métodos compatíveis satisfaz
o contrato. As implementações concretas ainda assim herdam explicitamente o
respectivo Protocol, tornando a relação "implementa a interface" visível no
código. Todos são ``runtime_checkable`` para permitir ``isinstance``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Protocol, runtime_checkable

from core.algorithms.analysis_result import AnalysisResult


@runtime_checkable
class MetricsRepository(Protocol):
    """Exporta métricas por deputado e por aresta para um formato tabular."""

    def export_deputy_metrics(self, deputies: list, year: int) -> Path: ...

    def export_coauthorship_metrics(self, coauthorships: Iterable, year: int) -> Path: ...


@runtime_checkable
class DatabaseRepository(Protocol):
    """Persiste métricas por deputado em um banco consultável."""

    def export_deputy_metrics(self, deputies: list, year: int) -> Path: ...


@runtime_checkable
class GraphRepository(Protocol):
    """Exporta o grafo para um formato interoperável (ex.: GEXF, lido pelo Gephi)."""

    def export_gexf(self, graph: Any, year: int | None = None) -> Path: ...


@runtime_checkable
class AnalysisStore(Protocol):
    """Persiste e recarrega o resultado analítico agregado de um ano."""

    def save(self, result: AnalysisResult) -> Path: ...

    def load(self, year: int) -> AnalysisResult: ...
