"""Shared statistical helpers for correlation-based algorithms.

Kept intentionally minimal — only utilities that are genuinely reused across
more than one analytical module belong here (validation.py for label-permutation
tests, relatorship.py for PP3, etc.).
"""
from __future__ import annotations

from typing import Sequence

from scipy.stats import spearmanr

# Minimum number of paired samples required for a Spearman correlation to be
# meaningful. Below this, the coefficient is undefined or numerically unstable.
_MIN_SAMPLES_FOR_CORRELATION = 3


def spearman_or_nan(x: Sequence[float], y: Sequence[float]) -> float:
    """Return Spearman rho of ``x`` vs. ``y``, or NaN when it is undefined.

    NaN is returned when:

    * the paired sample has fewer than ``_MIN_SAMPLES_FOR_CORRELATION`` points;
    * ``scipy.stats.spearmanr`` yields NaN because one of the inputs is constant.
    """
    if len(x) < _MIN_SAMPLES_FOR_CORRELATION:
        return float("nan")
    rho, _ = spearmanr(x, y)
    # spearmanr yields NaN when one input is constant; propagate it explicitly.
    return float(rho) if rho == rho else float("nan")


def spearman_with_pvalue(x: Sequence[float], y: Sequence[float]) -> tuple[float, float]:
    """Return ``(rho, p_value)`` for the Spearman correlation of ``x`` vs. ``y``.

    Both values are NaN when the coefficient is undefined (see
    :func:`spearman_or_nan`).
    """
    if len(x) < _MIN_SAMPLES_FOR_CORRELATION:
        return float("nan"), float("nan")
    rho, p_value = spearmanr(x, y)
    if rho != rho:  # NaN check
        return float("nan"), float("nan")
    return float(rho), float(p_value)
