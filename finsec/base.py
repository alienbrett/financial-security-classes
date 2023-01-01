import datetime
import typing

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


class SecurityIdentifier(BaseObject):
    """Object that identifies an existing security. This should be like ISIN, FIGI, etc."""

    id_type: SecurityIdentifierType
    value: str

    class Config:
        use_enum_values = True


class SecurityReference(BaseObject):
    """References an existing security. Should be treated like pointer of sorts."""

    gsid: GSID
    ticker: Ticker


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
    identifiers: typing.List[SecurityIdentifier]

    primary_exchange: typing.Optional[Exchange]

    denominated_ccy: typing.Optional[SecurityReference]

    issuer: typing.Optional[str]
    description: typing.Optional[str]
    website: typing.Optional[str]

    # Security data valid and recent as-of this data
    as_of_date: typing.Optional[datetime.datetime]

    class Config:
        json_encoders = {
            datetime.date: lambda v: v.strftime("%Y-%m-%d"),
            datetime.datetime: lambda v: v.timestamp(),
            datetime.timedelta: pydantic.json.timedelta_isoformat,
        }
        use_enum_values = True
        extra = "forbid"

    def __init__(self, **data: typing.Any):
        super().__init__(**data)

        # Make sure gsid is explicitly set to None, not just unset
        data["gsid"] = data.get("gsid", None)

        self.ticker = self.ticker.strip().upper()


class Derivative(Security):
    """Derivative security, with some specified underlyer."""

    # Underlying that determines settlement of the contract
    underlying: SecurityReference = placeholder()

    settlement_type: SettlementType = placeholder()
    expiry_series_type: ExpirySeriesType = placeholder()
    expiry_time_of_day: ExpiryTimeOfDay = placeholder()

    expiry_date: datetime.date
    expiry_datetime: typing.Optional[datetime.datetime]

    # The multiplier vs underlier
    multiplier: Multiplier = placeholder()

    @pydantic.validator("expiry_date")
    def date_str_to_datetime_date(cls, v):
        if isinstance(v, datetime.date):
            return v
        elif isinstance(v, str):
            return pd.to_datetime(v).date.to_pydatetime()
        else:
            raise TypeError("expiry_date has unknown type {0}".format(type(v)))


class Future(Derivative):
    """Exchange-traded future object, derived from some underlying."""

    tick_size: CurrencyQty = placeholder()


class Option(Derivative):
    """Option object, derived from some underlying."""

    option_flavor: OptionFlavor = placeholder()
    option_exercise: OptionExerciseStyle = placeholder()

    strike: CurrencyQty = placeholder()


AnySecurity = typing.Union[
    Option,
    Future,
    Security,
    Derivative,
]
