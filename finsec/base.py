import datetime
from typing import Any, List, Optional, Union

import pandas as pd
import pydantic
import bson

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
from .utils import placeholder
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
