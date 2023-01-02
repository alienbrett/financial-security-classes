import datetime
from typing import List, Optional, Union

from .base import Future, Security, SecurityIdentifier, SecurityReference
from .constructors import create_reference_from_security
from .enums import (
    GSID,
    CurrencyQty,
    ExpirySeriesType,
    ExpiryTimeOfDay,
    Multiplier,
    SecuritySubtype,
    SecurityType,
    SettlementType,
    Ticker,
)
from .exchanges import Exchange
from .misc import get_deriv_currency, get_future_exercise, get_settlement_type


def NewFuture(
    ticker: Ticker,
    underlying_security: Security,
    tick_size: CurrencyQty,
    multiplier: Multiplier,
    expiry_time_of_day: ExpiryTimeOfDay,
    expiry_date: datetime.date,
    settlement_type: SettlementType = SettlementType.UNKNOWN,
    expiry_series_type: ExpirySeriesType = ExpirySeriesType.UNKNOWN,
    currency: Union[Security, SecurityReference, None] = None,
    primary_exc: Optional[Exchange] = None,
    description: Optional[str] = None,
    website: Optional[str] = None,
    gsid: GSID = None,
    identifiers: Optional[List[SecurityIdentifier]] = None,
) -> Future:

    if identifiers is None:
        identifiers = []

    settlement_type = get_settlement_type(underlying_security, settlement_type)
    underlying_ref = create_reference_from_security(underlying_security)
    currency = get_deriv_currency(underlying_security, currency)

    exercise = get_future_exercise(
        expiry_date,
        settlement_type=settlement_type,
        expiry_series_type=expiry_series_type,
        expiry_time_of_day=expiry_time_of_day,
    )

    return Future(
        ticker=ticker,
        gsid=gsid,
        underlying=underlying_ref,
        tick_size=tick_size,
        multiplier=multiplier,
        security_type=SecurityType.DERIVATIVE,
        security_subtype=SecuritySubtype.FUTURE,
        exercise=exercise,
        primary_exchange=primary_exc,
        description=description,
        identifiers=identifiers,
        website=website,
        issuer=None,
        denominated_ccy=currency,
    )
