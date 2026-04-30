"""Data model for a co-authorship relationship between deputies."""
from dataclasses import dataclass


@dataclass
class CoauthorshipEdge:
    """Represents a weighted co-authorship relationship between two deputies.
    
    Attributes:
        source_id: ID of first deputy
        target_id: ID of second deputy
        raw_weight: Total co-authored propositions before normalization
        normalized_strength: Normalized weight after accounting for number of authors
    """
    source_id: int
    target_id: int
    raw_weight: int
    normalized_strength: float = 0.0
