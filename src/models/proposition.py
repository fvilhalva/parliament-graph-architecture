"""Data model for a legislative proposition."""
from dataclasses import dataclass
from typing import List


@dataclass
class Proposition:
    """Represents a legislative proposition (bill, amendment, etc.).
    
    Attributes:
        id: Unique identifier from Câmara API
        year: Year of proposition submission
        author_ids: List of deputy IDs who authored this proposition
        proposition_type: Type code ('PL' for Bill, 'PLP' for Complementary Law, 'PEC' for Amendment)
    """
    id: int
    year: int
    author_ids: List[int]
    proposition_type: str = ""
