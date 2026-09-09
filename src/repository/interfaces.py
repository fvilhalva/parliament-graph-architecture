"""Contracts (interfaces) for the persistence layer.

Defines, via ``typing.Protocol``, the contracts that the repository layer
offers to the layers above it. The pipeline (high-level policy) depends on
these abstractions -- not on the concrete implementations -- realising the
Dependency Inversion Principle (DIP): swapping CSV for another tabular format,
or SQLite for another database, requires no change to the core, only a new
implementation that satisfies the same contract.

Protocols are structural: any class with compatible methods satisfies the
contract. The concrete implementations still inherit their Protocol explicitly,
so the "implements the interface" relationship is visible in the code. All are
``runtime_checkable`` to allow ``isinstance`` checks.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Protocol, runtime_checkable

from core.algorithms.analysis_result import AnalysisResult


@runtime_checkable
class MetricsRepository(Protocol):
    """Exports per-deputy and per-edge metrics to a tabular format."""

    def export_deputy_metrics(self, deputies: list, year: int) -> Path: ...

    def export_coauthorship_metrics(self, coauthorships: Iterable, year: int) -> Path: ...


@runtime_checkable
class DatabaseRepository(Protocol):
    """Persists per-deputy metrics in a queryable database."""

    def export_deputy_metrics(self, deputies: list, year: int) -> Path: ...


@runtime_checkable
class GraphRepository(Protocol):
    """Exports the graph to an interoperable format (e.g. GEXF, read by Gephi)."""

    def export_gexf(self, graph: Any, year: int | None = None) -> Path: ...


@runtime_checkable
class AnalysisStore(Protocol):
    """Persists and reloads the aggregated analysis result for a year."""

    def save(self, result: AnalysisResult) -> Path: ...

    def load(self, year: int) -> AnalysisResult: ...
