from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Expense:
    """
    Represents a single expense entry.
    """
    id: Optional[int]
    spender: str
    date: date
    shop: str
    amount: float
