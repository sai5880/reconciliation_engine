from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List

from pydantic import BaseModel


class Transaction(BaseModel):

    id: str

    amount: Decimal

    date: Optional[datetime]

    description: str

    reference: Optional[str] = None

    source: str

    metadata: Dict = {}


class MatchResult(BaseModel):

    bank_id: str

    gl_id: str

    bank_description: str

    gl_description: str

    confidence: float

    matched_rules: List[str]

    explanation: Dict