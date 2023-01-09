import datetime
from typing import Optional, Union

from .base import (
    AmericanOptionExercise,
    EuropeanOptionExercise,
    ExerciseDatetime,
    ForwardExercise,
    OptionExercise,
    Security,
    SecurityReference,
)
from .constructors import create_reference_from_security
from .enums import (
    ExpirySeriesType,
    ExpiryTimeOfDay,
    OptionExerciseStyle,
    OptionFlavor,
    SecuritySubtype,
    SecurityType,
    SettlementType,
)
from .exceptions import InvalidSettlementType, UnknownDenominatedCurrency


def is_physical_settlement_available(security: Security) -> bool:
    # security_type = security.security_type
    security_subtype = security.security_subtype

    if security_subtype in (
        SecuritySubtype.DERIVED_INDEX,
        SecuritySubtype.TERM_RATE,
        SecuritySubtype.OVERNIGHT_RATE,
        SecuritySubtype.UNKNOWN,
    ):
        return False
    else:
        return True


def get_flavor(callput: Union[str, OptionFlavor]) -> OptionFlavor:
    if isinstance(callput, OptionFlavor):
        flavor = callput

    elif isinstance(callput, str):
        good_callput = callput.strip().lower()
        if good_callput == "call":
            flavor = OptionFlavor.CALL
        elif good_callput == "put":
            flavor = OptionFlavor.PUT
        else:
            raise ValueError("Unknown callput type: {0}".format(callput))
    return flavor


def get_settlement_type(
    underlyer: Security, settlement_type: Optional[SettlementType]
) -> SettlementType:
    """Returns the implied settlement type available for a given underlyer and specified type."""
    if is_physical_settlement_available(underlyer):
        if settlement_type is None or settlement_type == SettlementType.UNKNOWN:
            raise InvalidSettlementType(
                "Must specify settlement type, since underlying permits physical delivery"
            )
    else:
        if settlement_type == SettlementType.PHYSICAL:
            raise InvalidSettlementType("Cannot physically-settle a derived index")
        else:
            settlement_type = SettlementType.CASH
    return settlement_type


def get_future_exercise(
    expiry_date: Union[datetime.date, datetime.datetime, str],
    settlement_type: SettlementType,
    expiry_time_of_day: ExpiryTimeOfDay = ExpirySeriesType.UNKNOWN,
    expiry_series_type: ExpirySeriesType = ExpirySeriesType.UNKNOWN,
) -> ForwardExercise:
    """Returns the exercise object from supplied info."""
    if isinstance(expiry_date, str):
        expiry_date = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
        expiry_datetime = None

    elif isinstance(expiry_date, datetime.datetime):
        expiry_datetime = expiry_date
        expiry_date = expiry_date.date()
    elif isinstance(expiry_date, datetime.date):
        expiry_date = expiry_date
        expiry_datetime = None

    exercise = ExerciseDatetime(
        expiry_date=expiry_date,
        expiry_datetime=expiry_datetime,
        expiry_time_of_day=expiry_time_of_day,
        expiry_series_type=expiry_series_type,
        settlement_type=settlement_type,
    )

    res = ForwardExercise(exercise=exercise)
    return res


def get_option_exercise(
    expiry_date: Union[datetime.date, datetime.datetime, str],
    style: OptionExerciseStyle,
    settlement_type: SettlementType,
    expiry_time_of_day: ExpiryTimeOfDay = ExpirySeriesType.UNKNOWN,
    expiry_series_type: ExpirySeriesType = ExpirySeriesType.UNKNOWN,
) -> OptionExercise:
    """Returns the exercise object from supplied info."""
    if isinstance(expiry_date, str):
        expiry_date = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
        expiry_datetime = None

    elif isinstance(expiry_date, datetime.datetime):
        expiry_datetime = expiry_date
        expiry_date = expiry_date.date()
    elif isinstance(expiry_date, datetime.date):
        expiry_date = expiry_date
        expiry_datetime = None

    exercise = ExerciseDatetime(
        expiry_date=expiry_date,
        expiry_datetime=expiry_datetime,
        expiry_time_of_day=expiry_time_of_day,
        expiry_series_type=expiry_series_type,
        settlement_type=settlement_type,
    )

    if style == OptionExerciseStyle.AMERICAN:
        res = AmericanOptionExercise(style=style, exercise=exercise)
    elif style == OptionExerciseStyle.EUROPEAN:
        res = EuropeanOptionExercise(style=style, exercise=exercise)

    return res


def determine_option_subtype(
    underlying_security: Security, currency: Security
) -> SecuritySubtype:
    """Returns the option subtype implied from underlyer and supplied currency."""
    lookup = {
        (SecurityType.INDEX, SecurityType.CURRENCY): SecuritySubtype.INDEX_OPTION,
        (SecurityType.EQUITY, SecurityType.CURRENCY): SecuritySubtype.EQUITY_OPTION,
        (SecurityType.CURRENCY, SecurityType.CURRENCY): SecuritySubtype.CURRENCY_OPTION,
    }
    return lookup[(underlying_security.security_type, currency.security_type)]


def get_deriv_currency(
    underlying_security: Security, currency: Optional[Security] = None
) -> SecurityReference:
    """Returns the derivative currency implied from underlyer and supplied currency."""
    if currency is None:
        if underlying_security.denominated_ccy is None:
            raise UnknownDenominatedCurrency(
                "Must declare denominated currency, if not supplied by underlier"
            )
        else:
            currency = underlying_security.denominated_ccy

    elif isinstance(currency, Security):
        currency = create_reference_from_security(currency)

    return currency
