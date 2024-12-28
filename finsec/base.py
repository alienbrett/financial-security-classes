import datetime
import decimal
from typing import Any, List, Optional, Union, Dict

import pandas as pd
import numpy as np
import pydantic
import bson
import uuid

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
from .utils import placeholder, format_number
from .format import pretty_print_security

# from .misc import is_physical_settlement_available


BaseObject = pydantic.BaseModel


class standard_model_config:
    json_encoders = {
        bson.ObjectId: str,
    #     # datetime.date: lambda v: v.strftime("%Y-%m-%d"),
    #     # datetime.datetime: lambda v: v.timestamp(),
    #     # datetime.timedelta: pydantic.json.timedelta_isoformat,
    #     # datetime.timedelta: pydantic.json.timedelta_seconds,
    }
    use_enum_values = True
    extra = "forbid"


class SecurityIdentifier(BaseObject):
    """Object that identifies an existing security. This should be like ISIN, FIGI, etc."""

    id_type: SecurityIdentifierType
    value: str

    class Config(standard_model_config):
        pass

    # class Config:
    #     use_enum_values = True


class SecurityReference(BaseObject):
    """References an existing security. Should be treated like pointer of sorts."""

    gsid: GSID
    ticker: Ticker
    security_type: SecurityType
    security_subtype: SecuritySubtype


class Security(BaseObject):
    """Foundational financial security object."""

    # Application-level globally unique security id
    # Burden is on user to assign these in unique way,
    # if user chooses to use this
    gsid: GSID

    # The common ticker name
    # Different vendors may use different variations,
    #    but they'll be responsible for formatting correctly given this object
    ticker: Ticker

    security_type: SecurityType
    security_subtype: SecuritySubtype
    identifiers: List[SecurityIdentifier]

    primary_exchange: Optional[Exchange] = None

    denominated_ccy: Optional[SecurityReference] = None

    issuer: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None

    # Security data valid and recent as-of this data
    as_of_date: Optional[datetime.datetime] = None
    # unique id that identifies this id
    version_id: Optional[GSID] = None

    class Config(standard_model_config):
        pass

    def __init__(self, **data: Any):
        super().__init__(**data)

        # Make sure gsid is explicitly set to None, not just unset
        data["gsid"] = data.get("gsid", None)

        self.ticker = self.ticker.strip().upper()
    
    # validate so that SecurityType, SecuritySubtype aren't integers, but converted to proper enums
    @pydantic.validator("security_type")
    def validate_security_type(cls, v):
        if isinstance(v, int):
            return SecurityType(v)
        return v
    
    @pydantic.validator("security_subtype")
    def validate_security_subtype(cls, v):
        if isinstance(v, int):
            return SecuritySubtype(v)
        return v
    
    __repr__ = pretty_print_security


class ExerciseDatetime(BaseObject):
    """Encodes information about a single exercise/expiration date/time a derivative."""

    expiry_date: datetime.date
    expiry_datetime: Optional[datetime.datetime] = None
    settlement_type: SettlementType = SettlementType.UNKNOWN
    expiry_time_of_day: ExpiryTimeOfDay = ExpiryTimeOfDay.UNKNOWN
    expiry_series_type: ExpirySeriesType = ExpirySeriesType.UNKNOWN

    @pydantic.validator("expiry_date")
    def date_str_to_datetime_date(cls, v):
        if isinstance(v, datetime.date):
            return v
        elif isinstance(v, str):
            return pd.to_datetime(v).date.to_pydatetime()
        else:
            raise TypeError("expiry_date has unknown type {0}".format(type(v)))


class DerivativeExercise(BaseObject):
    exercise: Union[List[ExerciseDatetime], ExerciseDatetime]
    class Config(standard_model_config):
        pass


class ForwardExercise(DerivativeExercise):
    exercise: ExerciseDatetime


class OptionExercise(DerivativeExercise):
    exercise: Union[List[ExerciseDatetime], ExerciseDatetime]
    style: OptionExerciseStyle

    @pydantic.validator("exercise")
    def check_exercise(cls, v, values):
        if isinstance(v, list):
            if len(v) > 1:
                if values["style"] != OptionExerciseStyle.BERMUDAN:
                    raise ValueError(
                        "OptionExercise with multiple exercise dates must be BERMUDAN style"
                    )
            return v
        else:
            return v


def AmericanOptionExercise(exercise: ExerciseDatetime) -> OptionExercise:
    return OptionExercise(
        exercise=exercise,
        style=OptionExerciseStyle.AMERICAN,
    )

def EuropeanOptionExercise(exercise: ExerciseDatetime) -> OptionExercise:
    return OptionExercise(
        exercise=exercise,
        style=OptionExerciseStyle.EUROPEAN,
    )

def BermudanOptionExercise(exercise: List[ExerciseDatetime]) -> OptionExercise:
    return OptionExercise(
        exercise=exercise,
        style=OptionExerciseStyle.BERMUDAN,
    )


class Derivative(Security):
    """Derivative security, with some specified underlyer."""

    underlying: SecurityReference = placeholder()
    multiplier: Multiplier = placeholder()
    exercise: DerivativeExercise = placeholder()


class Future(Derivative):
    """Exchange-traded future object, derived from some underlying."""

    tick_size: CurrencyQty = placeholder()
    exercise: ForwardExercise = placeholder()


class Option(Derivative):
    """Option object, derived from some underlying."""

    strike: CurrencyQty = placeholder()
    option_flavor: OptionFlavor = placeholder()
    exercise: OptionExercise = placeholder()
    # option_exercise: OptionExerciseStyle = placeholder()



AnySecurity = Union[
    Option,
    Future,
    Security,
    Derivative,
]


class AbstractPosition(pydantic.BaseModel):
    '''Base class for positions in securities.'''
    pass


class Position(AbstractPosition):
    '''Holds position information for some security.'''
    security:AnySecurity
    quantity:CurrencyQty=1
    
    @pydantic.field_validator("quantity", mode="before")
    def validate_quantity(cls, value)->CurrencyQty:
        '''Checks that the quantity is a CurrencyQty object.'''
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

    def __add__(self, other):
        '''Adds two positions together.'''
        if isinstance(other, Position):
            if self.security == other.security:
                return Position(security=self.security, quantity=self.quantity + other.quantity)
            else:
                raise ValueError("Cannot add two positions of different securities.")
        elif isinstance(other, (int, float, np.int64, np.int32, np.int16, np.int8, np.float64, np.float32, np.float16, decimal.Decimal)):
            return Position(security=self.security, quantity=self.quantity + other)
        else:
            raise TypeError(f"Cannot add Position and {type(other)}")

    def __mul__(self, other):
        '''Multiplies a position by a scalar.'''
        if isinstance(other, (int, float, np.int64, np.int32, np.int16, np.int8, np.float64, np.float32, np.float16, decimal.Decimal)):
            return Position(security=self.security, quantity=self.quantity * other)
        else:
            raise TypeError(f"Cannot multiply Position and {type(other)}")

    def __neg__(self):
        return Position(security=self.security, quantity=-self.quantity)




class Portfolio(AbstractPosition):
    '''Holds a portfolio of positions.'''
    positions:List[Position]

    # def __str__(self)->str:
    #     return f"Portfolio({len(self.positions)} x positions ({s}))"

    def __repr__(self)->str:
        s = ', '.join([ pos._core_post_str() for pos in self.positions ])
        return f"Portfolio({s})"

    @property
    def quantity_vector(self)->np.ndarray:
        '''Returns a numpy array of quantities for each position in the portfolio.'''
        return np.array([pos.quantity for pos in self.positions]).astype(float)
    
    @classmethod
    def build(cls, securities:List[AnySecurity], quantities:List[CurrencyQty])->"Portfolio":
        '''Creates a portfolio from a list of securities and quantities.'''
        positions = [Position(security=sec, quantity=qty) for sec, qty in zip(securities, quantities)]
        self = cls(positions=positions)
        return self
    
    def get_by_ticker(self, ticker:str)->Optional[Position]:
        return next((pos for pos in self.positions if pos.security.ticker == ticker), None)
    def get_by_gsid(self, gsid:GSID)->Optional[Position]:
        return next((pos for pos in self.positions if pos.security.gsid == gsid), None)
    
    def __getitem__(self, key:Union[int, slice, str, GSID]):
        '''Returns the position at the given index.'''
        if isinstance(key, (int, slice)):
            return self.positions[key]
        return self.get_by_ticker(key) or self.get_by_gsid(key)
    def __len__(self):
        '''Returns the number of positions in the portfolio.'''
        return len(self.positions)
    def __iter__(self):
        '''Iterates over the positions in the portfolio.'''
        return iter(self.positions)
    def __contains__(self, item):
        '''Checks if the given item is in the portfolio.'''
        return item in self.positions
    def __mul__(self, other):
        if isinstance(other, (int, float, np.int64, np.int32, np.int16, np.int8, np.float64, np.float32, np.float16, decimal.Decmial)):
            positions = [Position(security=pos.security, quantity=pos.quantity * other) for pos in self.positions]
            return Portfolio(positions=positions)
        else:
            raise TypeError(f"Cannot multiply Portfolio and {type(other)}")
    def __add__(self, other):
        '''Adds two portfolios together.'''
        if isinstance(other, Portfolio):
            positions = self.positions + other.positions
            return Portfolio(positions=positions)
        else:
            raise TypeError(f"Cannot add Portfolio and {type(other)}")
    def __neg__(self):
        return Portfolio(positions=[-pos for pos in self.positions])
    
    def _group_by_underlyer(self, gsid_not_ticker:bool)->Union[
        Dict[str, List[AbstractPosition]],
        Dict[GSID, List[AbstractPosition]],
    ]:
        '''Groups the positions by the underlyer of each position.'''
        group_dict = {}
        for pos in self.positions:
            # key = pos.security.underlying.gsid if gsid_not_ticker else pos.security.underlying.ticker
            und_sec = pos.security.underlying if hasattr(pos.security, 'underlying') else pos.security
            key = und_sec.gsid if gsid_not_ticker else und_sec.ticker
            group_dict[key] = group_dict.get(key, []) + [pos]
        # return group_dict
        return { k: Portfolio(positions=v) for k, v in group_dict.items() }
    
    def group_by_ticker(self)->Dict[str, List[AbstractPosition]]:
        '''Groups the positions by the underlyer ticker of each position.'''
        return self._group_by_underlyer(gsid_not_ticker=False)

    def group_by_gsid(self)->Dict[GSID, List[AbstractPosition]]:
        '''Groups the positions by the underlyer GSID of each position.'''
        return self._group_by_underlyer(gsid_not_ticker=True)

    def to_ticker_dict(self)->Dict[str, CurrencyQty]:
        '''Returns a dictionary representation of the portfolio.'''
        return { pos.security.ticker: pos.quantity for pos in self.positions }
    def to_gsid_dict(self)->Dict[GSID, CurrencyQty]:
        '''Returns a dictionary representation of the portfolio.'''
        return { pos.security.gsid: pos.quantity for pos in self.positions }

    def get_by_underlyer_ticker(self, ticker:str)->"Portfolio":
        '''Returns a portfolio of positions with the given underlyer ticker.'''
        positions = []
        for pos in self.positions:
            if (pos.security.ticker == ticker) or \
                hasattr(pos.security, 'underlying') and (pos.security.underlying.ticker == ticker):
                positions.append(pos)
        return Portfolio(positions=positions)