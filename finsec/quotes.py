import datetime
import typing
from decimal import Decimal

import pydantic

# from .base import Option, Security, SecurityIdentifier, SecurityReference
# from .constructors import create_reference_from_security
# from .enums import (
#     CurrencyQty,
#     ExpirySeriesType,
#     ExpiryTimeOfDay,
#     Multiplier,
#     OptionExerciseStyle,
#     OptionFlavor,
#     SecuritySubtype,
#     SecurityType,
#     SettlementType,
# )
# from .enums import *
from .exceptions import MissingTimezone
from .exchanges import Exchange
from .utils import placeholder

BaseObject = pydantic.BaseModel


def ensure_timezone(v: datetime.datetime) -> datetime.datetime:
    if v is not None:
        if v.tzinfo is not None:
            return v
    raise MissingTimezone("quote must have timezone-aware timestamp")


class AbstractQuote(BaseObject):
    exchange: typing.Optional[Exchange] = None

    class Config:
        json_encoders = {
            datetime.datetime: lambda v: v.timestamp(),
        }
        use_enum_values = True
        extra = "forbid"


class AbstractSnapshot(AbstractQuote):
    timestamp: datetime.datetime = placeholder()

    @pydantic.validator("timestamp")
    def timestamp_must_have_timezone(cls, v: datetime.datetime):
        return ensure_timezone(v)


class AbstractBar(AbstractQuote):
    start_timestamp: datetime.datetime = placeholder()
    end_timestamp: datetime.datetime = placeholder()

    @pydantic.validator("start_timestamp", "end_timestamp")
    def start_timestamp_must_have_timezone(cls, v: datetime.datetime):
        return ensure_timezone(v)


class HLS(AbstractBar):
    high: Decimal = placeholder()
    low: Decimal = placeholder()
    settle: Decimal = placeholder()


class OHLC(AbstractBar):
    open: Decimal = placeholder()
    high: Decimal = placeholder()
    low: Decimal = placeholder()
    close: Decimal = placeholder()


class OHLCWithVolume(OHLC):
    volume: Decimal = placeholder()


LevelOneQuote = None


class LevelOneQuote(AbstractSnapshot):
    bid: Decimal = placeholder()
    ask: Decimal = placeholder()

    bid_sz: int = placeholder()
    ask_sz: int = placeholder()

    last: typing.Optional[Decimal] = placeholder()
    last_sz: typing.Optional[int] = placeholder()
    last_time: typing.Optional[datetime.datetime] = placeholder()

    def __add__(self, obj: LevelOneQuote):
        if type(obj) == type(self):
            return LevelOneQuote(
                bid=self.bid + obj.bid,
                ask=self.ask + obj.ask,
                last=self.last + obj.last,
                bid_sz=min(self.bid_sz, obj.bid_sz),
                ask_sz=min(self.ask_sz, obj.ask_sz),
                last_sz=min(self.last_sz, obj.last_sz),
                last_time=max(self.last_time, obj.last_time),
                timestamp=max(self.timestamp, obj.timestamp),
            )
        else:
            raise TypeError("unknown object type {0}".format(type(obj)))

    def __sub__(self, obj):
        if type(obj) == type(self):
            return LevelOneQuote(
                bid=self.bid - obj.bid,
                ask=self.ask - obj.ask,
                last=self.last - obj.last,
                bid_sz=min(self.bid_sz, obj.ask_sz),
                ask_sz=min(self.ask_sz, obj.bid_sz),
                last_sz=min(self.last_sz, obj.last_sz),
                last_time=max(self.last_time, obj.last_time),
                timestamp=max(self.timestamp, obj.timestamp),
            )
        else:
            raise TypeError("unknown object type {0}".format(type(obj)))

    def __mul__(self, obj: Decimal):
        ret = self.copy()

        ret.bid *= obj
        ret.ask *= obj
        ret.last *= obj

        if obj < 0:
            ret.bid_sz, ret.ask_sz = ret.ask_sz, ret.bid_sz
            ret.bid, ret.ask = ret.ask, ret.bid

        return ret
