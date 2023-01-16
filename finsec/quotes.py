import datetime
import typing
from decimal import Decimal
from typing import Optional

import pydantic

from .enums import Size
from .exceptions import MissingTimezone
from .exchanges import Exchange
from .utils import mmax, mmin, placeholder

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
    volume: Optional[Decimal] = placeholder()

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
    open_interest: Optional[Decimal] = placeholder()


LevelOneQuote = None


class LevelOneQuote(AbstractSnapshot):
    bid: Decimal = placeholder()
    ask: Decimal = placeholder()

    bid_sz: Size = placeholder()
    ask_sz: Size = placeholder()

    last: typing.Optional[Decimal] = placeholder()
    last_sz: typing.Optional[Size] = placeholder()
    last_time: typing.Optional[datetime.datetime] = placeholder()

    def __add__(self, obj: LevelOneQuote):
        if type(obj) == type(self):
            use_last = self.last_time is not None and self.last_time == obj.last_time
            return LevelOneQuote(
                bid=self.bid + obj.bid,
                ask=self.ask + obj.ask,
                last=self.last + obj.last if use_last else None,
                bid_sz=mmin(self.bid_sz, obj.bid_sz),
                ask_sz=mmin(self.ask_sz, obj.ask_sz),
                last_sz=mmin(self.last_sz, obj.last_sz) if use_last else None,
                last_time=mmax(self.last_time, obj.last_time) if use_last else None,
                timestamp=mmax(self.timestamp, obj.timestamp),
            )
        else:
            raise TypeError("unknown object type {0}".format(type(obj)))

    def __sub__(self, obj):
        if type(obj) == type(self):
            use_last = self.last_time is not None and self.last_time == obj.last_time
            return LevelOneQuote(
                bid=self.bid - obj.ask,
                ask=self.ask - obj.bid,
                last=self.last - obj.last if use_last else None,
                bid_sz=mmin(self.bid_sz, obj.ask_sz),
                ask_sz=mmin(self.ask_sz, obj.bid_sz),
                last_sz=mmin(self.last_sz, obj.last_sz) if use_last else None,
                last_time=mmax(self.last_time, obj.last_time) if use_last else None,
                timestamp=mmax(self.timestamp, obj.timestamp),
            )
        else:
            raise TypeError("unknown object type {0}".format(type(obj)))

    def __mul__(self, obj: Decimal):
        ret = self.copy()

        for k in ("bid", "ask", "last"):
            v = getattr(ret, k)
            if v is not None:
                setattr(ret, k, v * obj)

        if obj < 0:
            ret.bid_sz, ret.ask_sz = ret.ask_sz, ret.bid_sz
            ret.bid, ret.ask = ret.ask, ret.bid

        return ret
