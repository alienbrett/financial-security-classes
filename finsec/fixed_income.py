from datetime import date
from decimal import Decimal
from typing import List, Optional, Union

from pydantic import BaseModel

# import finsec as fs
from .base import Security


class FixingIndex(Security):
    """Represents a reference index with a series of fixing values."""

    name: str  # Unique identifier for the index
    publisher: str  # Entity that publishes the fixings
    fixings: List[tuple[date, Decimal]]  # Historical fixings (date, value)


class Cashflow(Security):
    """A basic cashflow occurring on a specific date."""

    security: Security
    date: date
    amount: Decimal


class FixedLeg(Security):
    """A fixed cashflow leg for swaps or bonds."""

    notional: Decimal
    start_date: date
    end_date: date
    rate: Decimal  # Fixed rate as a decimal (e.g., 0.05 for 5%)
    payment_frequency: str  # Example: 'Annual', 'Semi-Annual', etc.


class FloatingLeg(FixedLeg):
    """A floating rate cashflow leg."""

    spread: Decimal  # Fixed spread over the floating rate
    gearing: Decimal  # Multiplier applied to the floating rate
    index: str  # Name of the FixingIndex used for rate determination


class Swap(Security):
    """A combination of a fixed leg and a floating leg."""

    fixed_leg: FixedLeg
    floating_leg: FloatingLeg
    notional: Decimal
    start_date: date
    end_date: date


class Bond(Security):
    """A standard bond structure."""

    issuer: str
    face_value: Decimal
    final_maturity: date
    coupon_leg: Union[FixedLeg, FloatingLeg]  # The bond pays fixed or floating interest
