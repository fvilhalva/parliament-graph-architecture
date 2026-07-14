"""Structural concentration of influence (research question PP1).

Answers "is power concentrated in a few parliamentarians?" by quantifying how
unequally a centrality metric is distributed across deputies. Two complementary
measures are reported:

* **Gini coefficient** — 0 means perfect equality (every deputy holds the same
  centrality); values close to 1 indicate that a tiny minority holds almost all
  of it.
* **Top-k share** — the fraction of the total metric held by the most central
  ``k%`` of deputies (e.g. "the top 5% hold 40% of all betweenness").

Neither measure depends on party labels; both are purely topological.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:  # pragma: no cover - import only for type hints
    from core.graph import ParliamentaryGraph


@dataclass
class ConcentrationResult:
    """Concentration of a single centrality metric across deputies.

    Attributes:
        metric: Name of the deputy attribute measured (e.g. ``betweenness_centrality``).
        gini: Gini coefficient in ``[0, 1]``.
        top_share: Mapping ``fraction -> share`` giving, for each top fraction
            (e.g. ``0.05``), the fraction of the total metric held by that
            top slice of deputies.
        n: Number of deputies considered.
    """

    metric: str
    gini: float
    top_share: dict[float, float] = field(default_factory=dict)
    n: int = 0

    def __str__(self) -> str:
        shares = ", ".join(
            f"top {int(frac * 100)}% = {share:.1%}" for frac, share in sorted(self.top_share.items())
        )
        return f"Concentration[{self.metric}]: Gini={self.gini:.3f} ({shares}; n={self.n})"


def gini(values: Sequence[float]) -> float:
    """Compute the Gini coefficient of a sequence of non-negative values.

    Uses the standard mean-absolute-difference formulation. Returns ``0.0`` for
    an empty sequence or when every value is zero (no inequality to measure).
    Negative values are not expected for centralities; they are clamped to zero.
    """
    xs = sorted(max(0.0, float(v)) for v in values)
    n = len(xs)
    total = sum(xs)
    if n == 0 or total == 0.0:
        return 0.0
    # G = sum_i (2i - n - 1) x_i / (n * sum x)   with i = 1..n over ascending xs
    weighted = sum((2 * (i + 1) - n - 1) * x for i, x in enumerate(xs))
    return weighted / (n * total)


def top_share(values: Sequence[float], fraction: float) -> float:
    """Return the share of the total held by the top ``fraction`` of ``values``.

    Args:
        values: Non-negative metric values (any order).
        fraction: Top slice to consider, in ``(0, 1]`` (e.g. ``0.05`` = top 5%).

    Returns:
        Fraction (``[0, 1]``) of the summed metric held by the ``ceil(fraction*n)``
        largest values. Returns ``0.0`` when the total is zero or there are no values.
    """
    xs = sorted((max(0.0, float(v)) for v in values), reverse=True)
    n = len(xs)
    total = sum(xs)
    if n == 0 or total == 0.0:
        return 0.0
    k = max(1, math.ceil(fraction * n))
    return sum(xs[:k]) / total


def assess_concentration(
    values: Sequence[float],
    metric: str,
    top_fractions: Sequence[float] = (0.05, 0.10, 0.20),
) -> ConcentrationResult:
    """Summarise the concentration of a metric distribution.

    Args:
        values: Non-negative metric values, one per deputy.
        metric: Human-readable name of the metric (stored on the result).
        top_fractions: Top slices to report shares for.

    Returns:
        A :class:`ConcentrationResult`.
    """
    return ConcentrationResult(
        metric=metric,
        gini=gini(values),
        top_share={frac: top_share(values, frac) for frac in top_fractions},
        n=len(values),
    )


def assess_graph_concentration(
    parliamentary_graph: "ParliamentaryGraph",
    metric: str = "betweenness_centrality",
    top_fractions: Sequence[float] = (0.05, 0.10, 0.20),
) -> ConcentrationResult:
    """Assess concentration of a deputy centrality attribute over the graph.

    Reads ``metric`` from every :class:`~models.deputy.Deputy` that is a node in
    the network. Centralities must already have been computed
    (see :meth:`ParliamentaryGraph.compute_all_centralities`).
    """
    values = [
        getattr(deputy, metric, 0.0)
        for node_id in parliamentary_graph.graph.nodes()
        if (deputy := parliamentary_graph.deputies.get(node_id)) is not None
    ]
    return assess_concentration(values, metric, top_fractions)
