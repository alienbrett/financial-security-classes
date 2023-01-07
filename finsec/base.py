import datetime
from typing import Any, List, Optional, Union

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
from .utils import placeholder

# from .misc import is_physical_settlement_available


BaseObject = pydantic.BaseModel


class standard_model_config:
    json_encoders = {
        datetime.date: lambda v: v.strftime("%Y-%m-%d"),
        datetime.datetime: lambda v: v.timestamp(),
        datetime.timedelta: pydantic.json.timedelta_isoformat,
    }
    use_enum_values = True
    extra = "forbid"


class SecurityIdentifier(BaseObject):
    """Object that identifies an existing security. This should be like ISIN, FIGI, etc."""

    id_type: SecurityIdentifierType
    value: str

    Config = standard_model_config

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

    primary_exchange: Optional[Exchange]

    denominated_ccy: Optional[SecurityReference]

    issuer: Optional[str]
    description: Optional[str]
    website: Optional[str]

    # Security data valid and recent as-of this data
    as_of_date: Optional[datetime.datetime]
    # unique id that identifies this id
    version_id: Optional[GSID] = None

    Config = standard_model_config

    def __init__(self, **data: Any):
        super().__init__(**data)

        # Make sure gsid is explicitly set to None, not just unset
        data["gsid"] = data.get("gsid", None)

        self.ticker = self.ticker.strip().upper()


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
    Config = standard_model_config


class ForwardExercise(DerivativeExercise):
    exercise: ExerciseDatetime


class OptionExercise(DerivativeExercise):
    style: OptionExerciseStyle


class AmericanOptionExercise(BaseObject):
    exercise: ExerciseDatetime
    style: OptionExerciseStyle = OptionExerciseStyle.AMERICAN


class EuropeanOptionExercise(BaseObject):
    exercise: ExerciseDatetime
    style: OptionExerciseStyle = OptionExerciseStyle.EUROPEAN


class BermudanOptionExercise(BaseObject):
    exercise: List[ExerciseDatetime]
    style: OptionExerciseStyle = OptionExerciseStyle.BERMUDAN


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
