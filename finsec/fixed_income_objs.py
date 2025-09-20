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

T = TypeVar('T')
ListOrT = Union[List[T], T]


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
        return self/other
    def __rfloordiv__(self, other: Union["QuoteWrapper", float]):
        return self//other
    def __rmod__(self, other: Union["QuoteWrapper", float]):
        return self%other
    def __rpow__(self, other: Union["QuoteWrapper", float]):
        return self**other

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
        return ql.CompositeQuote(q0, q1, op)
    else:
        return ql.DerivedQuote(q0, lambda xx: op(xx, q1))

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

class Calendar(enum.Enum):
    """Enum for QuantLib calendars."""
    NULL = "null"
    US_Settlement = "us/settlement"
    US_NYSE = "us/nyse"
    US_GovernmentBond = "us/government_bond"
    US_FederalReserve = "us/federal_reserve"
    US_NERC = "us/nerc"
    US_SOFR = "us/sofr"

    def as_ql(self) -> ql.Calendar:
        """Convert to QuantLib calendar."""
        return {
            Calendar.NULL: ql.NullCalendar(),
            Calendar.US_Settlement: ql.UnitedStates(ql.UnitedStates.Settlement),
            Calendar.US_NYSE: ql.UnitedStates(ql.UnitedStates.NYSE),
            Calendar.US_GovernmentBond: ql.UnitedStates(ql.UnitedStates.GovernmentBond),
            Calendar.US_FederalReserve: ql.UnitedStates(ql.UnitedStates.FederalReserve),
            Calendar.US_NERC: ql.UnitedStates(ql.UnitedStates.NERC),
            Calendar.US_SOFR: ql.UnitedStates(ql.UnitedStates.SOFR),
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
        return len(self.as_ql().dates())-1

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


    def get_period(self)->Period:
        if self.period is not None:
            return self.period
        elif self.freq is not None:
            if self.freq < 1:
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

        schedule = ql.Schedule(
            start, end,
            self.get_period().period,
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
        ql_dts = self.as_ql().dates()
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
    notional: ListOrT[decimal.Decimal]
    cpn: ListOrT[RateExpression]
    acc: AccrualInfo
    pay_delay: Period|None = None

    def notionals_array(self, as_float:bool=False)->List[decimal.Decimal]:
        if isinstance(self.notional, list):
            return [ float(x) if as_float else x for x in self.notional ]
        else:
            arr = [ float(self.notional) if as_float else self.notional ]
            return arr * len(self.acc)

    def rate_array(self,)->List[AbstractRateExpression]:
        if isinstance(self.cpn, list):
            return self.cpn
        else:
            return [self.cpn] * len(self.acc)

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



class Bond(pydantic.BaseModel):
    notional: decimal.Decimal
    leg: Leg
    settle_days: int
    credit_index: str|None = None
    face:decimal.Decimal=100
    settle: datetime.date|None=None
    redemption:decimal.Decimal|None=None

    def final_redemption(self)->decimal.Decimal:
        if self.redemption is None:
            return self.face
        return self.redemption

    def original_settle(self)->datetime.date:
        if self.settle is not None:
            return self.settle
        else:
            return self.leg.acc.start

    def as_quantlib(self):
        l = self.leg
        cpn_arr = l.rate_array()
        ## only handle fixed coupon for now
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

    def as_quantlib_helper(self)->Tuple[Quote, ql.FixedRateBondHelper]:
        q = Quote(quote=float(self.face))
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


class Swap(pydantic.BaseModel):
    legs : Tuple[Leg, Leg]

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

    def as_quantlib(
        self,
        index_lookup:Dict[
            Hashable,
            ql.IborIndex|ql.OvernightIndex
        ]|None=None,
    ):
        fix = self.fixed_leg
        flt = self.float_leg
        assert fix is not None, "swap doesnt have fixed leg"
        assert flt is not None, "swap doesnt have float leg"

        flt_index = index_lookup.get(flt.cpn.index)
        if flt_index is None:
            raise ValueError(f"Unknown index: {flt.cpn.index}")

        if isinstance(flt_index, ql.OvernightIndex):
            swp = ql.OvernightIndexedSwap(
                # Swap::Type type,
                # DoubleVector fixedNominals,
                # Schedule fixedSchedule,
                # Rate fixedRate,
                # DayCounter fixedDC,
                # DoubleVector overnightNominals,
                # Schedule overnightSchedule,
                # ext::shared_ptr< OvernightIndex > const & overnightIndex,
                # Spread spread=0.0,
                # Natural paymentLag=0,
                # BusinessDayConvention paymentAdjustment=Following,
                # Calendar paymentCalendar=Calendar(),
                # bool telescopicValueDates=False,
                # RateAveraging::Type averagingMethod=Compound
            )


    @classmethod
    def make_ois(
        cls,
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