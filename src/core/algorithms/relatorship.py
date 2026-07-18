"""Structural centrality vs. institutional influence (research question PP3).

Answers "does a deputy's structural position in the co-authorship network
predict real political influence?" by correlating a chosen centrality metric
(default: betweenness) against the number of proposition relatorships each
deputy received in the analysed scope.

The relatorship count is a proxy of institutional influence taken from the
Chamber's own record (``ultimoStatus_uriRelator``): only the leadership of a
committee or the presidency of the House can designate a relator, so having
been picked as relator repeatedly signals real political weight.

This module reads pre-aggregated ``relatorship_count`` values from each
:class:`Deputy`, populated by
:meth:`~core.graph.ParliamentaryGraph.assign_relatorship_counts`. Deputies
with zero relatorships are kept in the correlation — their absence from the
relator pool is itself information, not noise to be filtered.

Relators that were not nodes in the graph (e.g. senators writing back on
propositions of the Chamber; rare cases in the raw data) are counted
separately and reported alongside the correlation, since they represent
institutional influence that is invisible to the co-authorship network.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from core.algorithms.stats import spearman_with_pvalue

if TYPE_CHECKING:  # pragma: no cover - import only for type hints
    from core.graph import ParliamentaryGraph


@dataclass
class RelatorshipResult:
    """Correlation between a centrality metric and relatorship count.

    Attributes:
        metric: Centrality attribute correlated against relatorships
            (e.g. ``betweenness_centrality``).
        spearman_rho: Spearman rank correlation coefficient in ``[-1, 1]``.
            NaN when the sample is too small or one of the inputs is constant.
        p_value: Two-sided p-value of the correlation. NaN when ``spearman_rho``
            is NaN.
        n: Number of deputies considered (all graph nodes with a matching
            :class:`Deputy`).
        n_with_relatorship: Deputies with at least one relatorship in the year.
        n_off_graph_relators: Distinct relator ids that were not nodes in the
            network — reported for context, not part of the correlation.
        significant: True when ``p_value < alpha`` and the result is valid.
        alpha: Significance threshold used.
        valid: False when the correlation could not be computed (e.g. constant
            input or too few samples). ``significant`` is forced to False.
    """

    metric: str
    spearman_rho: float
    p_value: float
    n: int
    n_with_relatorship: int
    n_off_graph_relators: int
    significant: bool
    alpha: float = 0.05
    valid: bool = True

    def __str__(self) -> str:
        if not self.valid:
            return (
                f"Relatorship[{self.metric}]: INCONCLUSIVE "
                f"(n={self.n}, with_relatorship={self.n_with_relatorship})"
            )
        sig = "SIGNIFICANT" if self.significant else "NOT significant"
        return (
            f"Relatorship[{self.metric}] × relatorship_count: "
            f"rho={self.spearman_rho:.3f} (p={self.p_value:.4f}, {sig}; "
            f"n={self.n}, with_relatorship={self.n_with_relatorship}, "
            f"off_graph_relators={self.n_off_graph_relators})"
        )


def assess_graph_relatorship(
    parliamentary_graph: "ParliamentaryGraph",
    metric: str = "betweenness_centrality",
    alpha: float = 0.05,
) -> RelatorshipResult:
    """Correlate a Deputy centrality metric against ``relatorship_count``.

    Both attributes must already be populated on the deputies:

    * ``metric`` is expected to come from
      :meth:`ParliamentaryGraph.compute_all_centralities`;
    * ``relatorship_count`` is expected to come from
      :meth:`ParliamentaryGraph.assign_relatorship_counts`.

    Args:
        parliamentary_graph: The built graph.
        metric: Name of the Deputy attribute to correlate against relatorships.
            Defaults to ``"betweenness_centrality"`` — the metric with the
            strongest theoretical link to institutional broker roles.
        alpha: Significance threshold for the returned flag.

    Returns:
        A :class:`RelatorshipResult`. When the metric or relatorship column is
        constant (e.g. no deputy in the graph is a relator), the result is
        flagged ``valid=False``.
    """
    centrality_values: list[float] = []
    relatorship_values: list[int] = []
    n_with_relatorship = 0

    for node_id in parliamentary_graph.graph.nodes():
        deputy = parliamentary_graph.deputies.get(node_id)
        if deputy is None:
            continue
        centrality_values.append(float(getattr(deputy, metric, 0.0)))
        count = int(getattr(deputy, "relatorship_count", 0))
        relatorship_values.append(count)
        if count > 0:
            n_with_relatorship += 1

    n = len(centrality_values)
    n_off_graph_relators = int(parliamentary_graph.off_graph_relator_count)

    rho, p_value = spearman_with_pvalue(centrality_values, relatorship_values)

    # NaN check via self-comparison — rho != rho iff rho is NaN.
    valid = rho == rho and p_value == p_value
    significant = valid and p_value < alpha

    return RelatorshipResult(
        metric=metric,
        spearman_rho=rho if valid else float("nan"),
        p_value=p_value if valid else float("nan"),
        n=n,
        n_with_relatorship=n_with_relatorship,
        n_off_graph_relators=n_off_graph_relators,
        significant=significant,
        alpha=alpha,
        valid=valid,
    )
