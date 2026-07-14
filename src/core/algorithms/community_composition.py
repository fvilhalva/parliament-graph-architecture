"""Party composition of detected communities (research question PP2).

Answers "do the detected communities correspond to isolated parties or to
supra-party coalitions?" by cross-tabulating each community's members against
their ``party_code``.

For every community we compute its *purity*: the share of its members that
belong to its single largest party. A community made of one party has purity
1.0 (a "party" community); a community that mixes many parties has low purity
(a "coalition" community). Aggregating over the partition yields a global,
label-aware picture that complements the (label-free) modularity of H1.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import only for type hints
    from core.graph import ParliamentaryGraph


# A community is treated as a coalition when its largest party accounts for less
# than this share of its members.
_COALITION_PURITY_THRESHOLD = 0.5


@dataclass
class CommunityCompositionResult:
    """Party composition of a community partition.

    Attributes:
        num_communities: Number of communities considered (size >= min_size).
        num_multiparty: Communities containing more than one party.
        multiparty_fraction: ``num_multiparty / num_communities``.
        mean_purity: Size-weighted mean purity (share of each community held by
            its largest party), in ``[0, 1]``.
        coalition_fraction: Fraction of communities whose largest party holds
            less than half the members (i.e. genuine coalitions).
        details: Per-community breakdown, each a dict with ``size``,
            ``num_parties``, ``dominant_party`` and ``purity``.
    """

    num_communities: int
    num_multiparty: int
    multiparty_fraction: float
    mean_purity: float
    coalition_fraction: float
    details: list[dict] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        """Coarse label: are communities parties or coalitions?"""
        if self.num_communities == 0:
            return "indeterminado"
        if self.mean_purity >= 0.75:
            return "partidos"
        if self.mean_purity <= 0.5:
            return "coalizões"
        return "misto"

    def __str__(self) -> str:
        return (
            f"Community composition: {self.verdict} "
            f"(pureza média={self.mean_purity:.2f}, "
            f"multipartidárias={self.multiparty_fraction:.0%}, "
            f"coalizões={self.coalition_fraction:.0%}, "
            f"n_comunidades={self.num_communities})"
        )


def assess_community_composition(
    partition: dict[int, int],
    node_party: dict[int, str],
    min_size: int = 3,
) -> CommunityCompositionResult:
    """Cross-tabulate a community partition against party labels.

    Args:
        partition: Mapping ``{node_id: community_id}``.
        node_party: Mapping ``{node_id: party_code}``.
        min_size: Communities with fewer members than this are ignored, since
            purity is not meaningful for tiny groups.

    Returns:
        A :class:`CommunityCompositionResult`.
    """
    # Group members by community.
    communities: dict[int, list[int]] = {}
    for node_id, community_id in partition.items():
        communities.setdefault(community_id, []).append(node_id)

    details: list[dict] = []
    total_members = 0
    weighted_dominant = 0
    num_multiparty = 0
    num_coalition = 0

    for community_id, members in communities.items():
        size = len(members)
        if size < min_size:
            continue

        party_counts = Counter(node_party.get(node_id, "N/A") for node_id in members)
        dominant_party, dominant_count = party_counts.most_common(1)[0]
        num_parties = len(party_counts)
        purity = dominant_count / size

        details.append(
            {
                "community_id": community_id,
                "size": size,
                "num_parties": num_parties,
                "dominant_party": dominant_party,
                "purity": purity,
            }
        )

        total_members += size
        weighted_dominant += dominant_count
        if num_parties > 1:
            num_multiparty += 1
        if purity < _COALITION_PURITY_THRESHOLD:
            num_coalition += 1

    num_communities = len(details)
    if num_communities == 0:
        return CommunityCompositionResult(0, 0, 0.0, 0.0, 0.0, [])

    details.sort(key=lambda d: d["size"], reverse=True)
    return CommunityCompositionResult(
        num_communities=num_communities,
        num_multiparty=num_multiparty,
        multiparty_fraction=num_multiparty / num_communities,
        mean_purity=weighted_dominant / total_members,
        coalition_fraction=num_coalition / num_communities,
        details=details,
    )


def assess_graph_community_composition(
    parliamentary_graph: "ParliamentaryGraph",
    partition: dict[int, int],
    min_size: int = 3,
) -> CommunityCompositionResult:
    """Assess community composition using deputy party labels from the graph."""
    node_party = {
        node_id: deputy.party_code
        for node_id in parliamentary_graph.graph.nodes()
        if (deputy := parliamentary_graph.deputies.get(node_id)) is not None
    }
    return assess_community_composition(partition, node_party, min_size=min_size)
