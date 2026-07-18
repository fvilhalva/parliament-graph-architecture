"""Data model for a legislative proposition."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Proposition:
    """Represents a legislative proposition (bill, amendment, etc.).

    Attributes:
        id: Unique identifier from Câmara API.
        year: Year of proposition submission.
        author_ids: List of deputy IDs who authored this proposition.
        proposition_type: Type code ('PL' for Bill, 'PLP' for Complementary
            Law, 'PEC' for Amendment, etc.).
        relator_id: Deputy ID of the designated relator for this proposition,
            or ``None`` when no relator was assigned. Extracted from
            ``ultimoStatus_uriRelator`` on the Chamber CSV.
    """
    id: int
    year: int
    author_ids: List[int]
    proposition_type: str = ""
    relator_id: Optional[int] = None
