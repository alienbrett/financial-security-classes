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
from .exceptions import InvalidSettlementType, UnknownDenominatedCurrency
from .exchanges import Exchange
from .misc import is_physical_settlement_available


def NewFuture(
    ticker: Ticker,
    underlying_security: Security,
    tick_size: CurrencyQty,
    multiplier: Multiplier,
    expiry_time_of_day: ExpiryTimeOfDay,
    expiry_date: datetime.date,
    expiry_datetime: Optional[datetime.datetime] = None,
    settlement_type: Optional[SettlementType] = None,
    expiry_series_type: Optional[ExpirySeriesType] = None,
    currency: Union[Security, SecurityReference, None] = None,
    primary_exc: Optional[Exchange] = None,
    description: Optional[str] = None,
    website: Optional[str] = None,
    gsid: GSID = None,
    identifiers: Optional[List[SecurityIdentifier]] = None,
) -> Future:
    if identifiers is None:
        identifiers = []
    # Will link against this underlier
    # If underlier is an index, then settlement inferred as cash-settled
    # If none, this is set to UNKNOWN
    # Currency will be used, if it cannot be inferred from underlying

    if is_physical_settlement_available(underlying_security):
        if settlement_type is None:
            raise InvalidSettlementType(
                "Must specify settlement type, since underlying permits physical delivery"
            )
    else:

        if settlement_type == SettlementType.PHYSICAL:
            raise InvalidSettlementType("Cannot physically-settle a derived index")
        else:
            settlement_type = SettlementType.CASH

    if expiry_series_type is None:
        expiry_series_type = ExpirySeriesType.UNKNOWN

    underlying_ref = create_reference_from_security(underlying_security)

    if currency is None:
        if underlying_security.denominated_ccy is None:
            raise UnknownDenominatedCurrency(
                "Must declare denominated currency, if not supplied by underlier"
            )
        else:
            currency = underlying_security.denominated_ccy
    elif isinstance(currency, Security):
        currency = create_reference_from_security(currency)

    return Future(
        ticker=ticker,
        gsid=gsid,
        underlying=underlying_ref,
        tick_size=tick_size,
        multiplier=multiplier,
        security_type=SecurityType.DERIVATIVE,
        security_subtype=SecuritySubtype.FUTURE,
        settlement_type=settlement_type,
        expiry_series_type=expiry_series_type,
        expiry_time_of_day=expiry_time_of_day,
        expiry_date=expiry_date,
        expiry_datetime=expiry_datetime,
        primary_exchange=primary_exc,
        description=description,
        identifiers=identifiers,
        website=website,
        issuer=None,
        denominated_ccy=currency,
    )
