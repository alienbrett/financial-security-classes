import datetime
import decimal
import uuid
from typing import Any, Dict, List, Optional, Union, Self

import operator
import bson
import numpy as np
import pandas as pd
import pydantic

from .enums import (
    GSID,
    CurrencyQty,
    ExpirySeriesType,
    ExpiryTimeOfDay,
    Multiplier,
    OptionExerciseStyle,
    OptionFlavor,
    SecurityIdentifierType,
    SecuritySubtype,
    SecurityType,
    SettlementType,
    Ticker,
)
from .exchanges import Exchange
from .format import pretty_print_security
from .security import AnySecurity
from .utils import format_number, placeholder

NumericType = (
    int,
    float,
    np.int64,
    np.int32,
    np.int16,
    np.int8,
    np.float64,
    np.float32,
    np.float16,
    decimal.Decimal,
)

class AbstractPosition(pydantic.BaseModel):
    """Base class for positions in securities."""

    pass


class Position(AbstractPosition):
    """Holds position information for some security."""

    security: AnySecurity
    quantity: CurrencyQty = 1

    @pydantic.field_validator("quantity", mode="before")
    def validate_quantity(cls, value) -> CurrencyQty:
        """Checks that the quantity is a CurrencyQty object."""
        if isinstance(value, (np.int64, np.int32, np.int16, np.int8)):
            value = int(value)
        elif isinstance(value, (np.float64, np.float32, np.float16)):
            value = float(value)
        return CurrencyQty(value)

    def _core_post_str(self):
        qty_str = format_number(self.quantity, 3)
        return f"{qty_str} x {self.security.ticker}"

    def __repr__(self):
        core_post_str = self._core_post_str()
        return f"Position({core_post_str})"

    def __sub__(self, other):
        return self + (-other)
    def __radd__(self, other):
        return self + other
    def __rsub__(self, other):
        return -(self-other)
    
    def __truediv__(self, other):
        return self._op(other, operator.truediv)

    def __add__(self, other):
        """Adds two positions together."""
        if isinstance(other, Position):
            if self.security == other.security:
                return Position(
                    security=self.security,
                    quantity=self.quantity + other.quantity
                )
            else:
                # raise ValueError("Cannot add two positions of different securities.")
                return Portfolio(positions=[self, other])
        elif isinstance( other, NumericType,):
            if not isinstance(other, decimal.Decimal):
                other = decimal.Decimal(other)
            return Position(security=self.security, quantity=self.quantity + other)
        else:
            raise TypeError(f"Cannot add Position and {type(other)}")

    def __mul__(self, other):
        """Multiplies a position by a scalar."""
        return self._op(other, operator.mul)

    def __pow__(self, other, op):
        """Exponentiates a position"""
        return self._op(other, operator.pow)

    def __abs__(self, other, op):
        """Abs-values a position"""
        return self._op(other, operator.abs)

    def _op(self, other, op):
        """Generically applies some scalar to a position"""
        if isinstance( other, NumericType,):
            if not isinstance(other, decimal.Decimal):
                other = decimal.Decimal(other)
            return Position(security=self.security, quantity=op(self.quantity,other))
        else:
            raise TypeError(f"Cannot perform math operations on Position and {type(other)}")

    def __neg__(self):
        return Position(security=self.security, quantity=-self.quantity)
    


class Portfolio(AbstractPosition):
    """Holds a portfolio of positions."""

    positions: List[Position]

    # def __str__(self)->str:
    #     return f"Portfolio({len(self.positions)} x positions ({s}))"
    @pydantic.model_validator(mode='after')
    def validate(obj)->Self:
        new_positions = []
        for p in obj.positions:
            if p.quantity != decimal.Decimal(0):
                new_positions.append(p)
        obj.positions = new_positions
        return obj

    def __repr__(self) -> str:
        s = ", ".join([pos._core_post_str() for pos in self.positions])
        return f"Portfolio({s})"

    @property
    def quantity_vector(self) -> np.ndarray:
        """Returns a numpy array of quantities for each position in the portfolio."""
        return np.array([pos.quantity for pos in self.positions]).astype(float)

    @classmethod
    def build(
        cls, securities: List[AnySecurity], quantities: List[CurrencyQty]
    ) -> "Portfolio":
        """Creates a portfolio from a list of securities and quantities."""
        positions = [
            Position(security=sec, quantity=qty)
            for sec, qty in zip(securities, quantities)
        ]
        self = cls(positions=positions)
        return self

    def get_by_ticker(self, ticker: str) -> Optional[Position]:
        return next(
            (pos for pos in self.positions if pos.security.ticker == ticker), None
        )

    def get_by_gsid(self, gsid: GSID) -> Optional[Position]:
        return next((pos for pos in self.positions if pos.security.gsid == gsid), None)

    def __getitem__(self, key: Union[int, slice, str, GSID]):
        """Returns the position at the given index."""
        if isinstance(key, (int, slice)):
            return self.positions[key]
        return self.get_by_ticker(key) or self.get_by_gsid(key)

    def __len__(self):
        """Returns the number of positions in the portfolio."""
        return len(self.positions)

    def __iter__(self):
        """Iterates over the positions in the portfolio."""
        return iter(self.positions)

    def __contains__(self, item):
        """Checks if the given item is in the portfolio."""
        return item in self.positions

    def __mul__(self, other):
        if isinstance( other, NumericType,):
            if not isinstance(other, decimal.Decimal):
                other = decimal.Decimal(other)
            positions = [
                Position(security=pos.security, quantity=pos.quantity * other)
                for pos in self.positions
            ]
            return Portfolio(positions=positions)
        else:
            raise TypeError(f"Cannot multiply Portfolio and {type(other)}")
    
    def __rmul__(self, other):
        return self * other
    
    def __sub__(self, other):
        if isinstance(other, Portfolio):
            return self + (-other)
        if isinstance(other, Position):
            return self + Position(security=other.security, quantity=-other.quantity)
        raise TypeError(f"Cannot subtract {type(other)} from Portfolio")

    def __add__(self, other):
        """Adds a position or another portfolio, then coalesces by GSID."""
        if isinstance(other, Portfolio):
            positions = self.positions + other.positions
        elif isinstance(other, Position):
            positions = self.positions + [other]
        else:
            raise TypeError(f"Cannot add Portfolio and {type(other)}")

        new_pos = {}
        for p in positions:
            k = p.security.gsid
            if k not in new_pos:
                new_pos[k] = p
            else:
                # relies on Position.__iadd__/__add__ to sum quantities
                new_pos[k] += p
        return Portfolio(positions=list(new_pos.values()))

    def __radd__(self, other):
        # lets sum([...], Portfolio(...)) work and supports Position + Portfolio
        if other == 0 or other is None:
            return self
        if isinstance(other, Portfolio):
            return other.__add__(self)
        if isinstance(other, Position):
            return self.__add__(other)
        return NotImplemented
    
    # def __sub__(self, other):
    #     return self + (-other)

    # def __add__(self, other):
    #     """Adds two portfolios together."""
    #     if isinstance(other, Portfolio):
    #         positions = self.positions + other.positions
    #         # res = Portfolio(positions=positions)
    #     if isinstance(other, Position):
    #         # res = self + Portfolio(positions=[other])
    #         positions = self.positions + [other]
    #     else:
    #         raise TypeError(f"Cannot add Portfolio and {type(other)}")
    #     new_pos = dict()
    #     for p in positions:
    #         k = p.security.gsid
    #         pp = new_pos.get(k, None)
    #         if pp is None:
    #             pp = p
    #         else:
    #             pp += p
    #         new_pos[k] = pp
    #     return Portfolio(positions=list(new_pos.values()))
    
    def __truediv__(self, other):
        if isinstance(other, NumericType):
            return Portfolio(positions=[pos/other for pos in self.positions])
        else:
            raise TypeError(f"Cannot divide portfolio by {type(other)}")
    
    def __rtruediv__(self, other):
        if isinstance(other, NumericType):
            return Portfolio(positions=[other/pos for pos in self.positions])
        else:
            raise TypeError(f"Cannot {type(other)} by Portfolio")
    
    def __neg__(self):
        return Portfolio(positions=[-pos for pos in self.positions])

    def _group_by_underlyer(
        self, gsid_not_ticker: bool
    ) -> Union[Dict[str, List[AbstractPosition]], Dict[GSID, List[AbstractPosition]],]:
        """Groups the positions by the underlyer of each position."""
        group_dict = {}
        for pos in self.positions:
            # key = pos.security.underlying.gsid if gsid_not_ticker else pos.security.underlying.ticker
            und_sec = (
                pos.security.underlying
                if hasattr(pos.security, "underlying")
                else pos.security
            )
            key = und_sec.gsid if gsid_not_ticker else und_sec.ticker
            group_dict[key] = group_dict.get(key, []) + [pos]
        # return group_dict
        return {k: Portfolio(positions=v) for k, v in group_dict.items()}

    def group_by_ticker(self) -> Dict[str, List[AbstractPosition]]:
        """Groups the positions by the underlyer ticker of each position."""
        return self._group_by_underlyer(gsid_not_ticker=False)

    def group_by_gsid(self) -> Dict[GSID, List[AbstractPosition]]:
        """Groups the positions by the underlyer GSID of each position."""
        return self._group_by_underlyer(gsid_not_ticker=True)

    def to_ticker_dict(self) -> Dict[str, CurrencyQty]:
        """Returns a dictionary representation of the portfolio."""
        return {pos.security.ticker: pos.quantity for pos in self.positions}

    def to_gsid_dict(self) -> Dict[GSID, CurrencyQty]:
        """Returns a dictionary representation of the portfolio."""
        return {pos.security.gsid: pos.quantity for pos in self.positions}

    def get_by_underlyer_ticker(self, ticker: str) -> "Portfolio":
        """Returns a portfolio of positions with the given underlyer ticker."""
        positions = []
        for pos in self.positions:
            if (
                (pos.security.ticker == ticker)
                or hasattr(pos.security, "underlying")
                and (pos.security.underlying.ticker == ticker)
            ):
                positions.append(pos)
        return Portfolio(positions=positions)
