import pydantic
BaseObject = pydantic.BaseModel

####################
import typing
import datetime
from decimal import Decimal

from .enums         import *
from .exceptions    import *
from .exchanges     import *
from .utils         import *



def ensure_timezone(v:datetime.datetime) -> datetime.datetime:
    if v is not None:
        if v.tzinfo is not None:
            return v
    raise MissingTimezone('quote must have timezone-aware timestamp')



class AbstractQuote(BaseObject):
    exchange    : typing.Optional[Exchange] = None

    class Config:
        json_encoders = {
            datetime.datetime   : lambda v: v.timestamp(),
        }
        use_enum_values = True
        extra   = 'forbid'


class AbstractSnapshot(AbstractQuote):
    timestamp : datetime.datetime   = placeholder()

    @pydantic.validator('timestamp')
    def timestamp_must_have_timezone(cls, v:datetime.datetime):
        return ensure_timezone(v)


class AbstractBar(AbstractQuote):
    start_timestamp : datetime.datetime = placeholder()
    end_timestamp   : datetime.datetime = placeholder()

    @pydantic.validator('start_timestamp', 'end_timestamp')
    def start_timestamp_must_have_timezone(cls, v:datetime.datetime):
        return ensure_timezone(v)


class OHLC(AbstractBar):
    open        : Decimal   = placeholder()
    high        : Decimal   = placeholder
    low         : Decimal   = placeholder()
    close       : Decimal   = placeholder()

class OHLCWithVolume(OHLC):
    volume      : Decimal    = placeholder()

class LevelOneQuote(AbstractSnapshot):
    bid         : Decimal           = placeholder()
    ask         : Decimal           = placeholder()

    bid_sz      : int               = placeholder()
    ask_sz      : int               = placeholder()

    last        : typing.Optional[Decimal]          = placeholder()
    last_sz     : typing.Optional[int]              = placeholder()
    last_time   : typing.Optional[datetime.datetime]= placeholder()

