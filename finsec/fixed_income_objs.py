import datetime
import decimal
import enum
import functools
import json
import logging
import operator
import os
from operator import add, mul, sub
from typing import *

import numpy as np
import pandas as pd
import pydantic
import QuantLib as ql

from .base import Security, SecurityReference
from .portfolio import Portfolio, Position

T = TypeVar('T')
ListOrT = Union[List[T], T]

IndexMap = NewType('IndexMap', Dict[Hashable, 'ql.InterestRateIndex'])

def loud_create(f, *args, **kwargs):
    print(f)
    for x in args:
        print(x)
    for k,v in kwargs.items():
        print(k,'->',v)
    return f(*args, **kwargs)

class Quote(pydantic.BaseModel):
    """Base wrapper for QuantLib quotes to enable Pythonic math operations."""
    quote: ql.SimpleQuote | ql.CompositeQuote | ql.DerivedQuote | float
    class Config:
        arbitrary_types_allowed = True
        ignored_types: set = (ql.QuoteHandle,)

    @pydantic.field_serializer("quote")
    def serialize_quote(self, v, _info):
        if isinstance(v, ql.SimpleQuote):
            return v.value()
        else:
            raise TypeError("Unsupported quote type for serialization.")

    @pydantic.field_validator("quote")
    def validate_quote(cls, v):
        if isinstance(v, float):
            return ql.SimpleQuote(v)
        return v

    @property
    def is_modifiable(self) -> bool:
        """Check if the quote is modifiable."""
        return isinstance(self.quote, ql.SimpleQuote)

    @property
    def handle(self)->ql.QuoteHandle:
        return ql.QuoteHandle(self.quote)

    def value(self) -> float:
        return self.quote.value()

    def setValue(self, value: float):
        if isinstance(self.quote, ql.SimpleQuote):
            self.quote.setValue(value)
        else:
            raise TypeError("Only SimpleQuote supports setting a value.")

    def __str__(self):
        return f"Quote({self.value()})"

    def __add__(self, other: Union["QuoteWrapper", float]):
        return Quote(quote=create_composite_quote(self.handle, other, operator.add))
    def __sub__(self, other: Union["QuoteWrapper", float]):
        return Quote(quote=create_composite_quote(self.handle, other, operator.sub))
    def __mul__(self, other: Union["QuoteWrapper", float]):
        return Quote(quote=create_composite_quote(self.handle, other, operator.mul))
    def __truediv__(self, other: Union["QuoteWrapper", float]):
        return Quote(quote=create_composite_quote(self.handle, other, operator.truediv))
    def __floordiv__(self, other: Union["QuoteWrapper", float]):
        return Quote(quote=create_composite_quote(self.handle, other, operator.floordiv))
    def __mod__(self, other: Union["QuoteWrapper", float]):
        return Quote(quote=create_composite_quote(self.handle, other, operator.mod))
    def __pow__(self, other: Union["QuoteWrapper", float]):
        return Quote(quote=create_composite_quote(self.handle, other, operator.pow))
    def __neg__(self):
        return Quote(quote=create_composite_quote(self.handle, -1, operator.mul))
    def __radd__(self, other: Union["QuoteWrapper", float]):
        return self+other
    def __rsub__(self, other: Union["QuoteWrapper", float]):
        return self-other
    def __rmul__(self, other: Union["QuoteWrapper", float]):
        return self*other
    def __rtruediv__(self, other: Union["QuoteWrapper", float]):
        return (self / other)**-1
    # def __rfloordiv__(self, other: Union["QuoteWrapper", float]):
    # def __rmod__(self, other: Union["QuoteWrapper", float]):
    #     return self%other
    # def __rpow__(self, other: Union["QuoteWrapper", float]):
    #     return self**other

    # def model_copy(self, **kwargs):
    #     values = self.model_dump()
    #     values.update(kwargs)
    #     return Quote(**values)

def create_composite_quote(
    x:ql.QuoteHandle|Quote,
    y:ql.QuoteHandle|Quote|float,
    op: Callable[[float, float], float]
)->ql.DerivedQuote|ql.CompositeQuote:
    q0 = x.handle if isinstance(x, Quote) else x
    q1 = y.handle if isinstance(y, Quote) else y

    if isinstance(q1, ql.QuoteHandle):
        q = ql.CompositeQuote(q0, q1, op)
    else:
        q = ql.DerivedQuote(q0, lambda xx: op(xx, q1))
    # _ = q.value()
    return q

class DayCount(enum.Enum):
    """Enum for QuantLib day counts."""
    Actual360 = "act/360"
    Actual365Fixed = "act/365f"
    ActualActual = "act/act"
    Thirty360 = "30/360"

    @property
    def as_ql(self) -> ql.DayCounter:
        """Convert to QuantLib day counter."""
        return {
            DayCount.Actual360: ql.Actual360(),
            DayCount.Actual365Fixed: ql.Actual365Fixed(),
            DayCount.ActualActual: ql.ActualActual(ql.ActualActual.ISDA),
            DayCount.Thirty360: ql.Thirty360(ql.Thirty360.BondBasis),
        }[self]

class Period(pydantic.BaseModel):
    """Wrapper for QuantLib periods."""
    period: ql.Period
    class Config:
        arbitrary_types_allowed = True

    @pydantic.field_validator("period")
    def validate_period(cls, v):
        if isinstance(v, ql.Period):
            return v
        return ql.Period(v)

    def __repr__(self):
        return self.period.__repr__()

    ## serialize, such that ql.Period(1, ql.Days) becomes 1D, ql.Period(10, ql.Months) becomes 10M, etc.
    @pydantic.field_serializer("period")
    def serialize_period(self, v: ql.Period) -> str:
        return self.period.__str__()

    @pydantic.field_validator('period', mode='before')
    def deserialize_period(cls, v: str) -> ql.Period:
        if isinstance(v, ql.Period):
            return v
        return ql.Period(v)
    
    @property
    def payments_per_year(self) -> int:
        p = self.period
        u = p.units()
        l = p.length()
        if u == ql.Years:
            return 1 // l if l > 1 else 1  # e.g., 1Y -> 1; 2Y would not be a valid coupon freq
        elif u == ql.Months:
            assert 12 % l == 0, "period units must divide 12 evenly"
            return 12 // l
        else:
            raise ValueError('Cannot produce frequency from this period')


def _make_calendar(class_name: str, market_attr: str | None = None):
    """
    Safely construct a QuantLib calendar.
    If the specific market enum doesn't exist in the current QL build,
    fall back to the class' default constructor.
    """
    CalClass = getattr(ql, class_name)
    if market_attr is None:
        return CalClass()
    # Try to fetch an inner enum like ql.Germany.Xetra, else fall back.
    try:
        market_enum = getattr(CalClass, market_attr)
        return CalClass(market_enum)
    except Exception:
        return CalClass()

class Calendar(enum.Enum):
    """Enum for QuantLib calendars.

    Notes for a US investor:
      - TARGET: Eurozone payments calendar (ECB/Eurosystem). Used for EUR OIS/IRS,
        govvie settlement (cash), and many EUR-denominated products.
      - UK_Exchange vs UK_Metals: LSE vs London bullion/Metals (LBMA-style) holidays differ.
      - Germany_Xetra/Eurex: Cash equities (Xetra/Frankfurt) vs derivatives (Eurex).
      - Japan: TSE/Tokyo business days (single market in QL); used for JPY IRS/JGBs.
      - HK_Exchange / SGX: Hong Kong and Singapore exchange schedules; useful for
        region-specific product calendars and valuation days.
      - China_SSE vs China_Interbank: Exchange vs CNY money-market/bond (IB) regimes.
    """

    # --- Null / US ----------------------------------------------------------
    NULL = "null"
    US_Settlement = "us/settlement"
    US_NYSE = "us/nyse"
    US_GovernmentBond = "us/government_bond"
    US_FederalReserve = "us/federal_reserve"
    US_NERC = "us/nerc"
    US_SOFR = "us/sofr"

    # --- Pan-EUR / Europe ---------------------------------------------------
    EU_TARGET = "eu/target"                       # Eurozone payments calendar (ECB)
    UK_Settlement = "uk/settlement"               # UK settlement days
    UK_Exchange = "uk/exchange"                   # London Stock Exchange
    UK_Metals = "uk/metals"                       # London metals (LBMA-like)

    DE_Settlement = "de/settlement"               # Germany settlement days
    DE_Frankfurt = "de/frankfurt"                 # Frankfurt Stock Exchange
    DE_Xetra = "de/xetra"                         # Xetra cash equities
    DE_Eurex = "de/eurex"                         # Eurex derivatives

    FR_Settlement = "fr/settlement"               # France settlement
    CH_Settlement = "ch/settlement"               # Switzerland settlement
    IT_Settlement = "it/settlement"               # Italy settlement (BTPs)
    # ES_Settlement = "es/settlement"               # Spain settlement (Bonos/Obligaciones)

    SE_Stockholm = "se/stockholm"                 # Sweden (Stockholm)
    NO_Oslo = "no/oslo"                           # Norway (Oslo)
    DK_Copenhagen = "dk/copenhagen"               # Denmark (Copenhagen)
    FI_Helsinki = "fi/helsinki"                   # Finland (Helsinki)

    # --- Americas (non-US) --------------------------------------------------
    CA_Settlement = "ca/settlement"               # Canada settlement
    CA_TSX = "ca/tsx"                              # Toronto Stock Exchange

    # --- APAC ---------------------------------------------------------------
    JP_Tokyo = "jp/tokyo"                          # Japan business days (TSE)
    HK_Exchange = "hk/exchange"                    # Hong Kong Exchange
    SG_SGX = "sg/sgx"                              # Singapore Exchange
    CN_SSE = "cn/sse"                              # China Shanghai Stock Exchange
    CN_Interbank = "cn/ib"                         # China Interbank (CNY MM/bonds)
    KR_KRX = "kr/krx"                              # Korea Exchange
    AU_ASX = "au/asx"                              # Australia (ASX)
    NZ_NZSE = "nz/nzse"                            # New Zealand (NZSE)

    @classmethod
    def lookup(cls):
        """Return a mapping from Calendar enum -> QuantLib calendar instance.

        Uses a defensive constructor to tolerate differences between QuantLib builds.
        """
        return {
            # --- Null / US ---
            Calendar.NULL: ql.NullCalendar(),
            Calendar.US_Settlement: ql.UnitedStates(ql.UnitedStates.Settlement),
            Calendar.US_NYSE: ql.UnitedStates(ql.UnitedStates.NYSE),
            Calendar.US_GovernmentBond: ql.UnitedStates(ql.UnitedStates.GovernmentBond),
            Calendar.US_FederalReserve: ql.UnitedStates(ql.UnitedStates.FederalReserve),
            Calendar.US_NERC: ql.UnitedStates(ql.UnitedStates.NERC),
            Calendar.US_SOFR: ql.UnitedStates(ql.UnitedStates.SOFR),

            # # --- Pan-EUR / Europe ---
            Calendar.EU_TARGET: ql.TARGET(),
            Calendar.UK_Settlement: ql.UnitedKingdom(ql.UnitedKingdom.Settlement),
            Calendar.UK_Exchange: ql.UnitedKingdom(ql.UnitedKingdom.Exchange),
            Calendar.UK_Metals: ql.UnitedKingdom(ql.UnitedKingdom.Metals),

            # # Germany: try specific markets, fall back if not in build
            Calendar.DE_Settlement: _make_calendar("Germany", "Settlement"),
            Calendar.DE_Frankfurt: _make_calendar("Germany", "FrankfurtStockExchange"),
            Calendar.DE_Xetra: _make_calendar("Germany", "Xetra"),
            Calendar.DE_Eurex: _make_calendar("Germany", "Eurex"),

            Calendar.FR_Settlement: _make_calendar("France", "Settlement"),
            Calendar.CH_Settlement: _make_calendar("Switzerland", "Settlement"),
            Calendar.IT_Settlement: _make_calendar("Italy", "Settlement"),
            # Calendar.ES_Settlement: _make_calendar("Spain", "Settlement"),

            # # Nordics (settlement/exchange naming varies; factory will fall back)
            Calendar.SE_Stockholm: _make_calendar("Sweden", "Stockholm"),
            Calendar.NO_Oslo: _make_calendar("Norway", "Oslo"),
            Calendar.DK_Copenhagen: _make_calendar("Denmark", "Copenhagen"),
            Calendar.FI_Helsinki: _make_calendar("Finland", "Helsinki"),

            # --- Americas (non-US) ---
            Calendar.CA_Settlement: _make_calendar("Canada", "Settlement"),
            Calendar.CA_TSX: _make_calendar("Canada", "TSX"),

            # --- APAC ---
            Calendar.JP_Tokyo: _make_calendar("Japan", None),  # single market in QL
            Calendar.HK_Exchange: _make_calendar("HongKong", "HKEx"),
            Calendar.SG_SGX: _make_calendar("Singapore", "SGX"),
            Calendar.CN_SSE: _make_calendar("China", "SSE"),
            Calendar.CN_Interbank: _make_calendar("China", "IB"),
            Calendar.KR_KRX: _make_calendar("SouthKorea", "KRX"),
            Calendar.AU_ASX: _make_calendar("Australia", None),
            Calendar.NZ_NZSE: _make_calendar("NewZealand", None),
        }

    @classmethod
    def from_ql(cls, obj):
        for k,v in cls.lookup().items():
            print(obj, v, k)
            if obj == v:
                return k

    def as_ql(self) -> ql.Calendar:
        """Convert to QuantLib calendar."""
        return self.lookup()[self]
    
    def bump(
        self,
        dt:datetime.date|List[datetime.date],
        period:Period|ql.Period|str
    )->List[datetime.date]:
        if not isinstance(dt, list):
            dt = [dt]
        if isinstance(period, Period):
            p = period.period
        else:
            p = Period(period=period).period
        ql_cal = self.as_ql()
        return [ ql_cal.advance(ql.Date.from_date(d), p).to_date() for d in dt ]
    
    @staticmethod
    def create_joint_calendar(c1, c2, join_holidays_not_bus_days:bool=False)->ql.JointCalendar:
        c1 = c1.as_ql() if isinstance(c1, Calendar) else c1
        c2 = c2.as_ql() if isinstance(c2, Calendar) else c2
        return ql.JointCalendar(
            c1, c2,
            ql.JoinHolidays if join_holidays_not_bus_days else ql.JoinBusinessDays
        )

class BusinessDayConvention(enum.Enum):
    """Enum for QuantLib business-day conventions with common short-codes."""
    unadjusted = "U"
    following = "F"
    modified_following = "MF"
    preceding = "P"
    modified_preceding = "MP"
    half_month_modified_following = "HMF"
    nearest = "N"

    @staticmethod
    def quantlib_dict()->Dict[str, int]:
        import QuantLib as ql
        return {
            "U": ql.Unadjusted,
            "F": ql.Following,
            "MF": ql.ModifiedFollowing,
            "P": ql.Preceding,
            "MP": ql.ModifiedPreceding,
            "HMF": ql.HalfMonthModifiedFollowing,
            "N": ql.Nearest,
        }

    def as_ql(self)->int:
        return self.quantlib_dict()[self.value]

    @classmethod
    def from_ql(cls, ql_obj: int)-> 'BusinessDayConvention':
        reverse_dict = {v: k for k, v in cls.quantlib_dict().items()}
        j = reverse_dict[ql_obj]
        return next(k for k in cls if k.value == j)

class AccrualSchedule(pydantic.BaseModel):
    start:  List[datetime.date]
    end:    List[datetime.date]
    frac:   List[float]

    def to_df(self)->pd.DataFrame:
        return pd.DataFrame({
            'start': self.start,
            'end': self.end,
            'frac': self.frac,
        })

class AccrualInfo(pydantic.BaseModel):
    start: datetime.date
    end: datetime.date|Period|str
    dc: DayCount
    freq: decimal.Decimal|None = None

    cal_accrual: Calendar = Calendar.NULL
    cal_pay: Calendar = Calendar.NULL
    period: Period|str|None = None
    bdc: BusinessDayConvention = BusinessDayConvention.following
    front_stub_not_back: bool = True
    eom: bool = False

    def __len__(self)->int:
        ql_sched = self.as_ql()
        if isinstance(ql_sched, tuple):
            return len(ql_sched)
        else:
            return len(ql_sched.dates())-1

    ## model validators
    @pydantic.model_validator(mode='after')
    def validate(cls, v):
        if isinstance(v.end, str):
            v.end = Period(period=ql.Period(v.end))

        if isinstance(v.period, str):
            v.period = Period(period=ql.Period(v.period))

        if v.freq is None and v.period is None:
            raise ValueError('Either freq or period must be provided.')
        return v

    def get_period(self)->Period|None:
        if self.period is not None:
            return self.period
        elif self.freq is not None:
            if self.freq == 0:
                return None
            elif self.freq < 1:
                x = f'{int(1/self.freq)}y'
            else:
                x = {
                    1: '1y',
                    2: '6m',
                    3: '4m',
                    4: '3m',
                    6: '2m',
                    12: '1m',
                    24: '2w',
                    52: '1w',
                }.get(self.freq)
                if x is None:
                    raise ValueError(f'Cannot convert to period, the frequency "{self.freq}"')
            return Period(period=ql.Period(x))
        else:
            raise ValueError('Either freq or period must be provided.')

    def as_ql(self):
        convention = self.bdc.as_ql()
        terminationDateConvention = self.bdc.as_ql()
        cal = self.cal_accrual.as_ql()
        start = ql.Date.from_date(self.start)

        if self.front_stub_not_back:
            rule = ql.DateGeneration.Backward
        else:
            rule = ql.DateGeneration.Forward

        if isinstance(self.end, datetime.date):
            end = ql.Date.from_date(self.end)
        elif isinstance(self.end, Period):
            end = cal.advance(start, self.end.period, terminationDateConvention, self.eom)

        p = self.get_period()
        ## check for flat/one-off frequency
        if p is None:
            schedule = ( start, end )
        else:
            schedule = ql.Schedule(
                start, end,
                p.period,
                cal,
                convention,
                terminationDateConvention,
                rule,
                self.eom,
            )

        return schedule

    def nodes(
            self,
            start:  datetime.date|None=None,
            end:    datetime.date|None=None,
        )->List[datetime.date]:
        qll = self.as_ql()
        if isinstance(qll, tuple) and len(qll) == 2:
            res = list(qll)
        else:
            ql_dts = qll.dates()
            res = []
            for ql_dt in ql_dts:
                dt = ql_dt.to_date()
                cond = (start is not None and dt < start) or (end is not None and dt > end)
                if not cond:
                    res.append(dt)
        return res

    def fraction( self, dt0:datetime.date, dt1:datetime.date, )->float:
        return self.dc.as_ql.yearFraction(
            ql.Date.from_date(dt0),
            ql.Date.from_date(dt1),
        )

    def schedule(
            self,
            start:  datetime.date|None=None,
            end:    datetime.date|None=None,
    )->AccrualSchedule:
        nodes = self.nodes(start=start,end=end)
        frac = [
            self.fraction( nodes[i-1], nodes[i])
            for i in range(1, len(nodes))
        ]
        return AccrualSchedule(
            start=nodes[:-1],
            end=nodes[1:],
            frac=frac,
        )

class ExprOperator(enum.Enum):
    ADD = 'ADD'
    SUB = 'SUB'
    MUL = 'MUL'
    NEG = 'NEG'
    MAX = 'MAX'
    MIN = 'MIN'

class ResetLookup(pydantic.BaseModel):
    resets: Dict[Hashable, Dict[datetime.date, decimal.Decimal]]
    @property
    def available_containers(self)->Set[Hashable]:
        return set(self.resets.keys())

class AbstractRateExpression(pydantic.BaseModel):
    def get_fixing(self, dt:datetime.date)->Optional[decimal.Decimal]:
        pass

    @staticmethod
    def wrap(x:int | decimal.Decimal | ListOrT["AbstractRateExpression"])->"AbstractRateExpression":
        if isinstance(x, decimal.Decimal):
            return FixedRate(rate=x)
        elif isinstance(x, int):
            return FixedRate(rate=decimal.Decimal(x))
        elif isinstance(x, AbstractRateExpression):
            return x
        else:
            raise ValueError(f'Unknown type : {type(x)}')

    def __add__(self, other: decimal.Decimal | ListOrT["AbstractRateExpression"]) -> "AbstractRateExpression":
        return CompositeRate( components = [self, self.wrap(other)], operator=ExprOperator.ADD)
    def __radd__(self, other: decimal.Decimal | ListOrT["AbstractRateExpression"]) -> "AbstractRateExpression":
        return CompositeRate( components = [self, self.wrap(other)], operator=ExprOperator.ADD)

    def __mul__(self, other: decimal.Decimal | ListOrT["AbstractRateExpression"]) -> "AbstractRateExpression":
        return CompositeRate( components = [self, self.wrap(other)], operator=ExprOperator.MUL)
    def __rmul__(self, other: decimal.Decimal | ListOrT["AbstractRateExpression"]) -> "AbstractRateExpression":
        return CompositeRate( components = [self, self.wrap(other)], operator=ExprOperator.MUL)

    def __sub__(self, other: decimal.Decimal | ListOrT["AbstractRateExpression"]) -> "AbstractRateExpression":
        return self + -self.wrap(other)
    def __rsub__(self, other: decimal.Decimal | ListOrT["AbstractRateExpression"]) -> "AbstractRateExpression":
        return -self + self.wrap(other)

    def __neg__(self) -> "AbstractRateExpression":
        return self * -1
    def __rneg__(self) -> "AbstractRateExpression":
        return self * -1



    @staticmethod
    def max(*args: ListOrT["AbstractRateExpression"]) -> "AbstractRateExpression":
        return CompositeRate( components = list(args), operator=ExprOperator.MAX)
    @staticmethod
    def min(*args: ListOrT["AbstractRateExpression"]) -> "AbstractRateExpression":
        return CompositeRate( components = list(args), operator=ExprOperator.MIN)

    # @property
    # def is_constant(self):
    #     raise NotImplementedError('child needs to instantiate constant')

FloatType_ = Literal['constant','overnight','term']
class AbstractFloatType(pydantic.BaseModel):
    type_:FloatType_
    pay_delay: Period|None = None
    # reset_lag: Period|None = None

class ConstantFloat(AbstractFloatType):
    '''CMS-style immediate cash payment'''
    type_:FloatType_='constant'

class OvernightFloat(AbstractFloatType):
    '''OIS style multi-reset'''
    type_:FloatType_='overnight'
    compounded_not_averaged:bool = True

class TermFloat(AbstractFloatType):
    '''forward-looking LIBOR-style'''
    type_:FloatType_='term'

FloatType = NewType('FloatType', ConstantFloat|OvernightFloat|TermFloat)

class FloatingRate(AbstractRateExpression):
    index: Hashable
    type_: FloatType

    is_constant:bool = False
    is_float:bool = True

    @property
    def is_compounded(self)->bool|None:
        if isinstance(self.type_,OvernightFloat):
            return self.type_.compounded_not_averaged

class FixedRate(AbstractRateExpression):
    rate: decimal.Decimal
    is_constant:bool = True
    is_float:bool = False
    def get_fixing(self, dt:datetime.date)->decimal.Decimal:
        return self.rate

class CompositeRate(AbstractRateExpression):
    components: List[AbstractRateExpression]
    operator: ExprOperator

    @property
    def is_constant(self):
        return all(c.is_constant for c in self.components)

    @property
    def is_float(self):
        return any(c.is_float for c in self.components)


    def get_fixing(self, dt:datetime.date)->decimal.Decimal:
        results = [c.get_fixing(dt) for c in self.components]
        match self.operator:
            case ExprOperator.ADD:
                return functools.reduce(add, results, decimal.Decimal(0))
            case ExprOperator.SUB:
                if len(self.components) != 2:
                    raise ValueError('SUB operator requires exactly 2 components.')
                return self.components[0].get_fixing(dt) - self.components[1].get_fixing(dt)
            case ExprOperator.MUL:
                return functools.reduce(mul, results, decimal.Decimal(1))
            case ExprOperator.MAX:
                return max(results)
            case ExprOperator.MIN:
                return min(results)
            case _:
                raise ValueError(f'Unknown operator: {self.operator}')

RateExpression = NewType('AnyAbstractRateExpression', FixedRate|FloatingRate|CompositeRate)

class Leg(pydantic.BaseModel):
    '''Encapsulates a single generic fixed-income coupon stream.
    '''
    ccy: Security|SecurityReference
    notional: ListOrT[decimal.Decimal]
    cpn: ListOrT[RateExpression]
    acc: AccrualInfo
    pay_delay: Period|None = None

    log: logging.Logger|None = pydantic.Field(
        default_factory=lambda: logging.getLogger('Leg'),
        exclude=True,
    )
    class Config:
        arbitrary_types_allowed = True

    def notionals_array(self, as_float:bool=False)->List[decimal.Decimal]:
        if isinstance(self.notional, list):
            return [ float(x) if as_float else x for x in self.notional ]
        else:
            arr = [ float(self.notional) if as_float else self.notional ]
            return arr * len(self.acc)

    def rate_array(self, as_float:bool|None=None)->List[AbstractRateExpression]:
        if isinstance(self.cpn, list):
            res = self.cpn
        else:
            res = [self.cpn] * len(self.acc)
        if as_float is not None:
            if as_float and self.cpn.is_constant:
                res = np.asarray([float(x.rate) for x in res])
        return res
    
    def get_dummy_leg(self)->ql.Leg:
        return ql.Leg([ql.SimpleCashFlow(0, ql.Settings.instance().evaluationDate)])

    @pydantic.field_validator('notional', mode='before', )
    @classmethod
    def validate_notional(cls, v:ListOrT[decimal.Decimal|int|float|str]):
        if isinstance(v, list):
            return [
                x if isinstance(x, decimal.Decimal) else decimal.Decimal(x)
                for x in v
            ]
        else:
            return v if isinstance(v, decimal.Decimal) else decimal.Decimal(v)

    @pydantic.model_validator(mode='after')
    @classmethod
    def validate(cls, v)->Self:
        assert len(v.notionals_array()) == len(v.acc)
        return v
    
    @property
    def pay_delay_days(self)->int:
        if self.pay_delay is None:
            return 0
        elif isinstance(self.pay_delay, Period):
            assert self.pay_delay.as_ql().units() == 0, "period type must be days, for pay delay"
            return self.pay_delay.as_ql().length()
    
    def get_float_index(self, 
        index_lookup:IndexMap|None=None,
    )->ql.InterestRateIndex|None:
        if self.cpn.is_float:
            if index_lookup is None:
                raise ValueError('must provide lookup')
            # flt_index = index_lookup.get(self.cpn.index)
            flt_index = index_lookup[self.cpn.index]
            if flt_index is None:
                raise ValueError(f"Unknown index: {self.cpn.index}")
            return flt_index

    def as_quantlib(
        self,
        index_lookup:IndexMap|None=None,
    ):
        if self.cpn.is_constant:
            ntnl_arr = self.notionals_array(as_float=True)
            rate_arr = self.rate_array(as_float=True)

            acc_sched = self.acc.as_ql()
            if isinstance(acc_sched, tuple):
                assert len(ntnl_arr) == 2
                assert len(rate_arr) == 2
                leg = ql.Leg([
                    ql.SimpleCashFlow(
                        # rate
                        ntnl_arr[-1] * rate_arr[-1],
                        # date
                        acc_sched[-1]
                    )
                ])
            else:
                leg = ql.FixedRateLeg(
                    acc_sched,
                    self.acc.dc.as_ql,
                    ntnl_arr,
                    rate_arr,
                    self.acc.bdc.as_ql(),
                    paymentCalendar=self.acc.cal_pay.as_ql(),
                    paymentLag=self.pay_delay_days,
                )
        elif self.cpn.is_float:
            idx = self.get_float_index(index_lookup=index_lookup)
            leg = ql.OvernightLeg(
            # leg = loud_create(ql.OvernightLeg,
                self.notionals_array(as_float=True),
                self.acc.as_ql(),
                idx,
                self.acc.dc.as_ql,
                self.acc.bdc.as_ql(),
                telescopicValueDates=False,
                averagingMethod=int(self.cpn.is_compounded),
                paymentCalendar=self.acc.cal_pay.as_ql(),
                paymentLag=self.pay_delay_days,
            )
        return leg

    def cashflows_df(
        self,
        index_lookup:IndexMap|None=None,
    )->pd.DataFrame:
        ql_leg = self.as_quantlib(index_lookup=index_lookup)
        rows = list()
        for cf in ql_leg:
            rows.append({
                'date': cf.date().to_date(),
                'amount': cf.amount(),
                'has_occurred': cf.hasOccurred(),
            })
        acc_df = self.acc.schedule().to_df()
        cashflow_df = pd.merge(
            acc_df,
            pd.DataFrame(rows),
            left_index=True,
            right_index=True,
            how='outer',
        ).set_index('date')
        cashflow_df['rate'] = cashflow_df['amount'] / cashflow_df['frac'] / float(self.notional)
        return cashflow_df

    def risk_builder(self, funding_index: str | ql.YieldTermStructureHandle, engine_args=None):
        if engine_args is None:
            engine_args = {}
        def f(index_map: IndexMap, funding_spec=funding_index):
            eval_dt = ql.Settings.instance().evaluationDate
            sett_dt = eval_dt
            # 1) Resolve funding curve handle
            if funding_spec is None:
                funding_spec = index_map.get_default_curve_by_ccy(ccy=self.ccy)

            if isinstance(funding_spec, str):
                funding_curve = index_map[funding_spec].forwardingTermStructure()
            else:
                funding_curve = funding_spec
            # assert not funding_curve.empty(), "Empty funding curve"
            self.log.debug( 'funding curve df: %f', funding_curve.discount( funding_curve.maxDate(),))

            # 2) Build QL instrument and engine
            ql_leg_obj = self.as_quantlib(index_lookup=index_map)
            ql_obj = ql.Swap(ql_leg_obj, self.get_dummy_leg())
            engine = ql.DiscountingSwapEngine(funding_curve, **engine_args)
            ql_obj.setPricingEngine(engine)

            # 3) Warm everything once so the first external call is correct
            ql_obj.recalculate()  # or ql_obj.NPV()

            # 4) Pin refs to avoid GC
            ql_obj._engine = engine
            ql_obj._funding_curve = funding_curve

            # 5) Return stable PV closure
            def g() -> float:
                # If you ever move Settings.evaluationDate elsewhere, re-pin here if needed
                # return ql_obj.NPV()
                return Position(
                    security=self.ccy,
                    quantity=ql_obj.NPV(),
                )
            return g, ql_obj
        return f

    

class Bond(pydantic.BaseModel):
    notional: decimal.Decimal
    leg: Leg
    settle_days: int
    credit_index: str|None = None
    face:decimal.Decimal=100
    settle: datetime.date|None=None
    redemption:decimal.Decimal|None=None

    log: logging.Logger|None = pydantic.Field(
        default_factory=lambda: logging.getLogger('Bond'),
        exclude=True,
    )
    class Config:
        arbitrary_types_allowed = True

    @property
    def ccy(self)->Security|SecurityReference:
        return self.leg.ccy

    def final_redemption(self)->decimal.Decimal:
        if self.redemption is None:
            return self.face
        return self.redemption

    def original_settle(self)->datetime.date:
        if self.settle is not None:
            return self.settle
        else:
            return self.leg.acc.start

    def as_quantlib(
        self,
        index_lookup:IndexMap|None=None,
    ):
        l = self.leg
        cpn_arr = l.rate_array()

        if all([x.is_constant for x in cpn_arr]):
            ql_sched = l.acc.as_ql()
            float_cpn_array = [float(x.rate) for x in cpn_arr]
            ql_bond = ql.FixedRateBond(
                # Integer settlementDays
                self.settle_days,
                # Real faceAmount
                float(self.notional),
                # Schedule schedule
                ql_sched,
                # DoubleVector coupons
                float_cpn_array,
                # DayCounter paymentDayCounter
                l.acc.dc.as_ql,
                # BusinessDayConvention paymentConvention=QuantLib::Following
                l.acc.bdc.as_ql(),
                # Real redemption=100.0
                float(self.final_redemption()),
                # Date issueDate=Date()
                ql.Date.from_date(self.original_settle()),
                # Calendar paymentCalendar=Calendar()
                l.acc.cal_pay.as_ql(),
                # Period exCouponPeriod=Period()
                # Calendar exCouponCalendar=Calendar()
                # BusinessDayConvention exCouponConvention=Unadjusted
                # bool exCouponEndOfMonth=False
            )
            return ql_bond
        else:
            raise NotImplementedError('need to implement non fixed-only bonds')

    def as_quantlib_helper(
        self,
        quote:Quote|None=None,
        index_lookup:IndexMap|None=None,
        fx_lookup:Any|None=None,
    )->Tuple[Quote, ql.FixedRateBondHelper]:
        if quote is None:
            q = Quote(quote=float(self.face))
        else:
            q = quote
        helper = ql.BondHelper(q.handle, self.as_quantlib())
        return q, helper

    def cashflows_df(self)->pd.DataFrame:
        rows = []
        for cf in self.as_quantlib().cashflows():
            rows.append({
                'date': cf.date().to_date(),
                'amount': cf.amount(),
                'has_occurred': cf.hasOccurred(),
            })
        pay_df = pd.DataFrame(rows)
        acc_df = self.leg.acc.schedule().to_df()

        cashflow_df = pd.merge(
            acc_df,
            pay_df,
            left_index=True,
            right_index=True,
            how='outer',
        )
        ntnl_mask = cashflow_df['frac'].isna()
        cashflow_df.loc[ntnl_mask, 'frac'] = 1.0
        cashflow_df['rate'] = cashflow_df['amount'] / cashflow_df['frac'] / float(self.notional)

        return cashflow_df
    
    def risk_builder(self, funding_index: str|ql.YieldTermStructureHandle|None=None, engine_args=None):
        if engine_args is None:
            engine_args = {}
        def f(index_map: IndexMap, funding_spec=funding_index):
            eval_dt = ql.Settings.instance().evaluationDate
            sett_dt = eval_dt
            # 1) Resolve funding curve handle
            if funding_spec is None:
                funding_spec = index_map.get_default_curve_by_ccy(ccy=ccy)
                # print('funding index?', funding_spec)
            if isinstance(funding_spec, str):
                funding_curve = index_map[funding_spec].forwardingTermStructure()
            else:
                funding_curve = funding_spec
            # assert not funding_curve.empty(), "Empty funding curve"
            self.log.debug( 'funding curve df: %f', funding_curve.discount( funding_curve.maxDate(),))

            # 2) Build QL instrument and engine
            ql_obj = self.as_quantlib(index_lookup=index_map)
            engine = ql.DiscountingBondEngine(funding_curve, **engine_args)
            ql_obj.setPricingEngine(engine)

            # 3) Warm everything once so the first external call is correct
            ql_obj.recalculate()  # or ql_obj.NPV()

            # 4) Pin refs to avoid GC
            ql_obj._engine = engine
            ql_obj._funding_curve = funding_curve

            # 5) Return stable PV closure
            def g() -> float:
                # If you ever move Settings.evaluationDate elsewhere, re-pin here if needed
                # return ql_obj.NPV()
                return Position(
                    security=self.ccy,
                    quantity=ql_obj.NPV(),
                )
            return g, ql_obj
        return f

class Swap(pydantic.BaseModel):
    legs : Tuple[Leg, Leg]

    log: logging.Logger|None = pydantic.Field(
        default_factory=lambda: logging.getLogger('Swap'),
        exclude=True,
    )
    class Config:
        arbitrary_types_allowed = True

    @property
    def fixed_leg(self)->Optional[Leg]:
        for x in self.legs:
            if x.cpn.is_constant:
                return x
        return None

    @property
    def float_leg(self)->Optional[Leg]:
        for x in self.legs:
            if x.cpn.is_float:
                return x
        return None
    
    @property
    def is_xccy(self)->bool:
        c0 = self.legs[0].ccy
        c1 = self.legs[1].ccy
        for x in ('ticker','gsid'):
            x0 = getattr(c0, x)
            x1 = getattr(c1, x)
            if x0 is not None and x1 is not None and x0 != x1:
                return True
        return False


    def as_quantlib(
        self,
        index_lookup:IndexMap|None=None,
        fx_lookup:Any|None=None,
    ):
        if self.is_xccy:
            swp = (
                (l.ccy, l.as_quantlib(index_lookup=index_lookup))
                for l in self.legs
            )

        else:
            fix = self.fixed_leg
            flt = self.float_leg
            assert fix is not None, "swap doesnt have fixed leg"
            assert flt is not None, "swap doesnt have float leg"

            flt_index = index_lookup.get(flt.cpn.index)
            if flt_index is None:
                raise ValueError(f"Unknown index: {flt.cpn.index}")
            
            fix_rate = fix.rate_array()
            assert all([x == fix_rate[0] for x in fix_rate])

            if flt.pay_delay is None:
                pay_delay_days = fix.pay_delay_days
            elif fix.pay_delay is None:
                pay_delay_days = flt.pay_delay_days
            else:
                pd0 = flt.pay_delay_days
                pd1 = fix.pay_delay_days
                assert pd0 == pd1
                pay_delay_days = pd0
            
            # telescopic_dates = True
            telescopic_dates = False

            if isinstance(flt_index, ql.OvernightIndex):
                swp = ql.OvernightIndexedSwap(
                # swp = loud_create(
                    # ql.OvernightIndexedSwap,
                    # Swap::Type type,
                    ql.OvernightIndexedSwap.Receiver,
                    # DoubleVector fixedNominals,
                    fix.notionals_array(as_float=True),
                    # Schedule fixedSchedule,
                    fix.acc.as_ql(),
                    # Rate fixedRate,
                    float(fix_rate[0].rate),
                    # DayCounter fixedDC,
                    fix.acc.dc.as_ql,
                    # DoubleVector overnightNominals,
                    -np.asarray(flt.notionals_array(as_float=True)),
                    # Schedule overnightSchedule,
                    flt.acc.as_ql(),
                    # ext::shared_ptr< OvernightIndex > const & overnightIndex,
                    flt_index,
                    # Spread spread=0.0,
                    0,
                    # Natural paymentLag=0,
                    pay_delay_days,
                    # BusinessDayConvention paymentAdjustment=Following,
                    fix.acc.bdc.as_ql(),
                    # Calendar paymentCalendar=Calendar(),
                    fix.acc.cal_pay.as_ql(),
                    # bool telescopicValueDates=False,
                    telescopic_dates,
                    # RateAveraging::Type averagingMethod=Compound
                    int(flt.cpn.is_compounded),
                )
        return swp

    def as_quantlib_helper(
        self,
        quote:Quote|None=None,
        index_lookup:IndexMap|None=None,
        fx_lookup:Any|None=None,
    )->Tuple[Quote, Any]:
        self.log.debug('Building actual ql helper')
        if self.is_xccy:
            helper = self.as_ql_fx_fwd_helper(
                quote=quote,
                index_lookup=index_lookup,
                fx_lookup=fx_lookup,
            )
        else:
            helper = self.as_ql_single_ccy_swap_helper(
                quote=quote,
                index_lookup=index_lookup,
            )
        return helper

    def as_ql_fx_fwd_helper(
        self,
        quote:Quote|None=None,
        index_lookup:IndexMap|None=None,
        fx_lookup:Any|None=None,
    )->Tuple[Quote, Any]:
        self.log.debug('Building FX swap helper')
        eval_dt = ql.Settings.instance().evaluationDate
        l_base = self.legs[0]
        l_quote = self.legs[1]

        q = Quote(quote=0) if quote is None else quote

        acc_sched = l_base.acc.as_ql()
        start = acc_sched[0]
        end = acc_sched[-1]
        bdc = l_base.acc.bdc.as_ql()
        eom = l_base.acc.eom

        # assert l_base.acc.get_period() == flt.acc.get_period()
        
        joint_cal = Calendar.create_joint_calendar( l_base.acc.cal_pay, l_quote.acc.cal_pay,)
        fixing_days = 1
        spot_dt = joint_cal.advance(eval_dt, fixing_days, ql.Days)
        adj_mat = joint_cal.adjust(end, bdc)

        bdays = joint_cal.businessDaysBetween(
            # from date
            spot_dt,
            # to date
            adj_mat,
            # include start
            False,
            # include end
            True,
        )
        tenor = ql.Period(bdays, ql.Days)

        funding_idx = index_lookup.get_default_curve_by_ccy(ccy=l_quote.ccy)
        self.log.debug('Using funding index for fx swap: %s', funding_idx)
        funding_curve = index_lookup[ funding_idx ].forwardingTermStructure()

        spot_quote = fx_lookup.get_fx_quote( l_base.ccy, l_quote.ccy)

        self.log.debug('Using spot fx: %f', spot_quote.value())
        self.log.debug('Using basis quote: %f', q.value())

        ## fx forward
        # assert l_base.rate == 
        helper = ql.FxSwapRateHelper(
        # helper = loud_create( ql.FxSwapRateHelper,
            # QuoteHandle fwdPoint,
            ## difference over spot rate, outright. not in pips or anything
            q.handle,
            # QuoteHandle spotFx,
            spot_quote.handle,
            # Period tenor,
            tenor,
            # Natural fixingDays,
            fixing_days,
            # Calendar calendar,
            joint_cal,
            # BusinessDayConvention convention,
            bdc,
            # bool endOfMonth,
            eom,
            # bool isFxBaseCurrencyCollateralCurrency,
            False,
            # YieldTermStructureHandle collateralCurve,
            funding_curve,
            # Calendar tradingCalendar=Calendar()
        )


        return q, helper




    def as_ql_single_ccy_swap_helper(
        self,
        quote:Quote|None=None,
        index_lookup:IndexMap|None=None,
    )->Tuple[Quote, Any]:
        self.log.debug('Building single-ccy swap helper')

        fix = self.fixed_leg
        flt = self.float_leg
        assert fix is not None, "swap doesnt have fixed leg"
        assert flt is not None, "swap doesnt have float leg"

        flt_index = index_lookup.get(flt.cpn.index)
        if flt_index is None:
            raise ValueError(f"Unknown index: {flt.cpn.index}")
        
        fix_rate = fix.rate_array()
        assert all([x == fix_rate[0] for x in fix_rate])

        if flt.pay_delay is None:
            pay_delay_days = fix.pay_delay_days
        elif fix.pay_delay is None:
            pay_delay_days = flt.pay_delay_days
        else:
            pd0 = flt.pay_delay_days
            pd1 = flt.pay_delay_days
            assert pd0 == pd1
            pay_delay_days = pd0
        
        telescopic_dates = False

        ## swaprate helper
        if quote is None:
            q = Quote(quote=0)
        else:
            q = quote

        fix_acc_sched = fix.acc.schedule()
        start = ql.Date.from_date(fix_acc_sched.start[0])
        end = ql.Date.from_date(fix_acc_sched.end[-1])

        assert fix.acc.get_period() == flt.acc.get_period()

        # fix_freq = period=fix.acc.get_period().payments_per_year
        # flt_freq = period=flt.acc.get_period().payments_per_year
        fix_freq = int(fix.acc.get_period().payments_per_year)
        flt_freq = int(flt.acc.get_period().payments_per_year)

        if isinstance(flt.cpn.type_, OvernightFloat):
            helper = ql.DatedOISRateHelper(
            # helper = loud_create(ql.DatedOISRateHelper,
                # Date startDate,
                start,
                # Date endDate,
                end,
                # QuoteHandle rate,
                q.handle,
                # ext::shared_ptr< OvernightIndex > const & index,
                flt_index,
                # YieldTermStructureHandle discountingCurve={},
                # disc_curve_use,
                ql.YieldTermStructureHandle(),
                # bool telescopicValueDates=False,
                telescopic_dates,
                # RateAveraging::Type averagingMethod=Compound,
                int(flt.cpn.is_compounded),
                # Integer paymentLag=0,
                pay_delay_days,
                # BusinessDayConvention paymentConvention=Following,
                fix.acc.bdc.as_ql(),
                # Frequency paymentFrequency=Annual,
                flt_freq,
                # Calendar paymentCalendar=Calendar(),
                fix.acc.cal_pay.as_ql(),
                # Spread overnightSpread=0.0,
                0,
                # ext::optional< bool > endOfMonth=ext::nullopt,
                fix.acc.eom,
                # ext::optional< Frequency > fixedPaymentFrequency=ext::nullopt,
                fix_freq,
                # Calendar fixedCalendar=Calendar(),
                fix.acc.cal_pay.as_ql(),
                # Natural lookbackDays=Null< Natural >(),
                0,
                # Natural lockoutDays=0,
                0,
                # bool applyObservationShift=False,
                False,
                # ext::shared_ptr< FloatingRateCouponPricer > const & pricer={}
            )
        return q, helper

    def cashflows_df(self, **kwargs)->pd.DataFrame:
        fix_df = self.fixed_leg.cashflows_df(**kwargs)
        flt_df = self.float_leg.cashflows_df(**kwargs)
        fix_df['fix'] = True
        flt_df['fix'] = False
        return pd.concat([fix_df,flt_df], axis=0).sort_index()

    @classmethod
    def make_ois(
        cls,
        ccy:Security|SecurityReference,
        start:datetime.date,
        end:Period|str|datetime.date,
        rate:float|decimal.Decimal,
        dc_fix:DayCount,
        dc_float:DayCount,
        freq_fix:int,
        freq_float:int,
        index:Hashable,
        notional:int=10000,
        cal_acc:Calendar=Calendar.NULL,
        cal_pay:Calendar=Calendar.NULL,
        bdc:BusinessDayConvention=BusinessDayConvention.following,
        pay_delay:Period|None=None,
        compounded_not_averaged:bool = True,
    )->"Swap":
        fixleg = Leg(
            ccy=ccy,
            notional=notional,
            cpn=FixedRate(rate=rate),
            acc=AccrualInfo(
                start=start,
                end=end,
	            dc=dc_fix,
	            freq=freq_fix,
	            bdc=bdc,
                cal_pay=cal_pay,
                cal_accrual=cal_acc,
            )
        )
        floatleg = Leg(
            ccy=ccy,
            notional=-notional,
            cpn=FloatingRate(
                index=index,
                type_=OvernightFloat(
                    compounded_not_averaged=compounded_not_averaged,
                    pay_delay=pay_delay,
                )
            ),
            acc=AccrualInfo(
                start=start,
				end=end,
				dc=dc_float,
				freq=freq_float,
				bdc=bdc,
                cal_pay=cal_pay,
                cal_accrual=cal_acc,
            )
        )
        swp = Swap(legs=(fixleg, floatleg))
        return swp

    def risk_builder(self, funding_index: str|ql.YieldTermStructureHandle|None=None, engine_args=None):
        if engine_args is None:
            engine_args = {}
        
        if self.is_xccy:
            fs = [
                l.risk_builder(funding_index=funding_index, engine_args=engine_args)
                for l in self.legs
            ]
            def f(index_map: IndexMap, funding_spec=funding_index):
                pv_funcs = []
                ql_objs = []
                for ff in fs:
                    pf, qlo = ff(index_map=index_map, funding_spec=funding_index)
                    pv_funcs.append(pf)
                    ql_objs.append(qlo)

                def g()->float:
                    return pv_funcs[0]() + pv_funcs[1]()
                
                return g, ql_objs

        else:
            def f(index_map: IndexMap, funding_spec=funding_index):
                nonlocal funding_index
                ccy = self.legs[0].ccy
                eval_dt = ql.Settings.instance().evaluationDate
                sett_dt = eval_dt
                # 1) Resolve funding curve handle
                if funding_spec is None:
                    funding_spec = index_map.get_default_curve_by_ccy(ccy=ccy)

                if isinstance(funding_spec, str):
                    funding_curve = index_map[funding_spec].forwardingTermStructure()
                else:
                    funding_curve = funding_spec
                # assert not funding_curve.empty(), "Empty funding curve"
                self.log.debug( 'funding curve df: %f', funding_curve.discount( funding_curve.maxDate(),))

                # 2) Build QL instrument and engine
                ql_obj = self.as_quantlib(index_lookup=index_map)
                engine = ql.DiscountingSwapEngine(funding_curve, sett_dt, eval_dt, **engine_args)
                ql_obj.setPricingEngine(engine)

                # 3) Warm everything once so the first external call is correct
                ql_obj.recalculate()  # or ql_obj.NPV()

                # 4) Pin refs to avoid GC
                ql_obj._engine = engine
                ql_obj._funding_curve = funding_curve

                # 5) Return stable PV closure
                def g() -> float:
                    # If you ever move Settings.evaluationDate elsewhere, re-pin here if needed
                    # return ql_obj.NPV()
                    return Position(
                        security=ccy,
                        quantity=ql_obj.NPV(),
                    )
                return g, ql_obj
        # f.funding_index = funding_index
        return f



FixedIncomeSecurity = Bond | Swap | Leg

__all__ = [
    'IndexMap',
    'Quote',
    'create_composite_quote',
    'DayCount',
    'Calendar',
    'Period',
    'BusinessDayConvention',
    'AccrualSchedule',
    'AccrualInfo',
    'ExprOperator',
    'ResetLookup',
    'AbstractRateExpression',
    'AbstractFloatType',
    'ConstantFloat',
    'OvernightFloat',
    'TermFloat',
    'FloatType',
    'FloatingRate',
    'FixedRate',
    'CompositeRate',
    'RateExpression',
    'Leg',
    'Bond',
    'Swap',
    'FixedIncomeSecurity',
]