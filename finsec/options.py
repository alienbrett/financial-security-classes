import datetime
from typing import List, Optional, Union

from .base import Option, Security, SecurityIdentifier, SecurityReference
from .constructors import create_reference_from_security
from .enums import (
    GSID,
    CurrencyQty,
    ExpirySeriesType,
    ExpiryTimeOfDay,
    Multiplier,
    OptionExerciseStyle,
    OptionFlavor,
    SecurityType,
    SettlementType,
)
from .exchanges import Exchange
from .misc import (
    determine_option_subtype,
    get_deriv_currency,
    get_flavor,
    get_option_exercise,
    get_settlement_type,
)
from .occ_symbology import option_format


def NewOption(
    underlying_security: Security,
    exercise_style: OptionExerciseStyle,
    multiplier: Multiplier,
    expiry_time_of_day: ExpiryTimeOfDay,
    strike: CurrencyQty,
    callput: str,
    expiry_date: Union[datetime.date, datetime.datetime, str],
    settlement_type: SettlementType = SettlementType.UNKNOWN,
    expiry_series_type: ExpirySeriesType = ExpirySeriesType.UNKNOWN,
    primary_exc: Optional[Exchange] = None,
    currency: Union[Security, SecurityReference, None] = None,
    identifiers: Optional[List[SecurityIdentifier]] = None,
    website: Optional[str] = None,
    gsid: GSID = None,
    description: Optional[str] = None,
) -> Option:

    if identifiers is None:
        identifiers = []

    underlying_ref = create_reference_from_security(underlying_security)
    flavor = get_flavor(callput)
    settlement_type = get_settlement_type(
        underlying_security,
        settlement_type,
    )

    exercise = get_option_exercise(
        expiry_date,
        style=exercise_style,
        settlement_type=settlement_type,
        expiry_series_type=expiry_series_type,
        expiry_time_of_day=expiry_time_of_day,
    )

    currency = get_deriv_currency(underlying_security, currency)
    occ_ticker = option_format(
        symbol=underlying_ref.ticker,
        exp_date=expiry_date,
        flavor="call" if flavor == OptionFlavor.CALL else "put",
        strike=strike,
    )
    sec_subtype = determine_option_subtype(
        underlying_security,
        currency,
    )

    return Option(
        gsid=gsid,
        ticker=occ_ticker,
        strike=strike,
        option_flavor=flavor,
        security_type=SecurityType.DERIVATIVE,
        security_subtype=sec_subtype,
        exercise=exercise,
        underlying=underlying_ref,
        multiplier=multiplier,
        denominated_ccy=currency,
        primary_exchange=primary_exc,
        identifiers=identifiers,
        website=website,
        description=description,
        issuer=None,
    )


def European(
    **kwargs,
) -> Option:
    """Creates option derivative. See NewOption for kwargs."""
    kwargs["exercise_style"] = OptionExerciseStyle.EUROPEAN
    return NewOption(**kwargs)


def American(
    **kwargs,
) -> Option:
    """Creates option derivative. See NewOption for kwargs."""
    kwargs["exercise_style"] = OptionExerciseStyle.AMERICAN
    return NewOption(**kwargs)
