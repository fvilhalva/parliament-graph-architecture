"""Tests for the AnalysisResult aggregator and Adjusted Rand Index helper."""

import math

import pytest

from core.algorithms.analysis_result import compute_adjusted_rand_index


class TestAdjustedRandIndex:
    def test_identical_partitions_are_one(self):
        p = {1: 0, 2: 0, 3: 1, 4: 1}
        assert compute_adjusted_rand_index(p, p) == pytest.approx(1.0)

    def test_relabeled_partitions_are_one(self):
        p = {1: 0, 2: 0, 3: 1, 4: 1}
        q = {1: 5, 2: 5, 3: 9, 4: 9}  # same partition, different labels
        assert compute_adjusted_rand_index(p, q) == pytest.approx(1.0)

    def test_disagreement_lowers_score(self):
        p = {1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 2}
        q = {1: 0, 2: 1, 3: 1, 4: 0, 5: 2, 6: 2}
        score = compute_adjusted_rand_index(p, q)
        assert score < 1.0

    def test_empty_intersection_is_zero(self):
        assert compute_adjusted_rand_index({1: 0}, {2: 0}) == 0.0

    def test_singleton_intersection_is_zero(self):
        # ARI is undefined for n < 2 pairs; we return 0.0 by convention.
        assert compute_adjusted_rand_index({1: 0, 2: 0}, {1: 0, 3: 1}) == 0.0

    def test_both_trivial_partitions_are_one(self):
        # Every node in the same community on both sides -> ARI defined as 1.
        p = {1: 0, 2: 0, 3: 0}
        q = {1: 7, 2: 7, 3: 7}
        assert compute_adjusted_rand_index(p, q) == pytest.approx(1.0)

    def test_only_shared_nodes_are_scored(self):
        p = {1: 0, 2: 0, 3: 1, 4: 1, 99: 5}  # 99 not in q
        q = {1: 0, 2: 0, 3: 1, 4: 1, 42: 6}  # 42 not in p
        # The intersection {1,2,3,4} is a perfect match.
        assert compute_adjusted_rand_index(p, q) == pytest.approx(1.0)
