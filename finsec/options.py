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
    SecuritySubtype,
    SecurityType,
    SettlementType,
)
from .exceptions import InvalidSettlementType, UnknownDenominatedCurrency
from .exchanges import Exchange
from .misc import is_physical_settlement_available
from .occ_symbology import option_format


def European(
    underlying_security: Security,
    multiplier: Multiplier,
    expiry_time_of_day: ExpiryTimeOfDay,
    strike: CurrencyQty,
    callput: str,
    expiry_date: datetime.date,
    expiry_datetime: Optional[datetime.datetime] = None,
    settlement_type: Optional[SettlementType] = None,
    expiry_series_type: Optional[ExpirySeriesType] = None,
    primary_exc: Optional[Exchange] = None,
    website: Optional[str] = None,
    gsid: GSID = None,
    currency: Union[Security, SecurityReference, None] = None,
    identifiers: Optional[List[SecurityIdentifier]] = None,
    **kwargs,
) -> Option:
    if identifiers is None:
        identifiers = []
    # Will link against this underlier
    # Callput should be in ('call','put')
    # If underlier is an index, then settlement inferred as cash-settled
    # If none, this is set to UNKNOWN
    # Currency will be used, if it cannot be inferred from underlying

    good_callput = callput.strip().lower()
    if good_callput == "call":
        flavor = OptionFlavor.CALL
    elif good_callput == "put":
        flavor = OptionFlavor.PUT
    else:
        raise ValueError("Unknown callput type: {0}".format(callput))

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

    if isinstance(expiry_date, str):
        expiry_date = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
    if expiry_datetime is not None and expiry_date is None:
        expiry_date = expiry_datetime.date()

    occ_ticker = option_format(
        symbol=underlying_ref.ticker,
        exp_date=expiry_date,
        flavor=callput,
        strike=strike,
    )

    if currency is None:
        if underlying_security.denominated_ccy is None:
            raise UnknownDenominatedCurrency(
                "Must declare denominated currency, if not supplied by underlier"
            )
        else:
            currency = underlying_security.denominated_ccy
    elif isinstance(currency, Security):
        currency = create_reference_from_security(currency)

    return Option(
        gsid=gsid,
        ticker=occ_ticker,
        strike=strike,
        option_flavor=flavor,
        security_type=SecurityType.DERIVATIVE,
        security_subtype=SecuritySubtype.EQUITY_OPTION,
        option_exercise=OptionExerciseStyle.EUROPEAN,
        settlement_type=settlement_type,
        expiry_date=expiry_date,
        expiry_datetime=expiry_datetime,
        expiry_time_of_day=expiry_time_of_day,
        underlying=underlying_ref,
        multiplier=multiplier,
        denominated_ccy=currency,
        expiry_series_type=expiry_series_type,
        primary_exchange=primary_exc,
        identifiers=identifiers,
        issuer=None,
        **kwargs,
    )


def American(
    underlying_security: Security,
    multiplier: Multiplier,
    expiry_time_of_day: ExpiryTimeOfDay,
    strike: CurrencyQty,
    callput: str,
    expiry_date: datetime.date,
    expiry_datetime: Optional[datetime.datetime] = None,
    settlement_type: Optional[SettlementType] = None,
    expiry_series_type: Optional[ExpirySeriesType] = None,
    primary_exc: Optional[Exchange] = None,
    currency: Union[Security, SecurityReference, None] = None,
    identifiers: Optional[List[SecurityIdentifier]] = None,
    website: Optional[str] = None,
    gsid: GSID = None,
    **kwargs,
) -> Option:
    # Will link against this underlier
    # Callput should be in ('call','put')
    # If underlier is an index, then settlement inferred as cash-settled
    # If none, this is set to UNKNOWN
    # Currency will be used, if it cannot be inferred from underlying
    if identifiers is None:
        identifiers = []

    good_callput = callput.strip().lower()
    if good_callput == "call":
        flavor = OptionFlavor.CALL
    elif good_callput == "put":
        flavor = OptionFlavor.PUT
    else:
        raise ValueError("Unknown callput type: {0}".format(callput))

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

    if isinstance(expiry_date, str):
        expiry_date = datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date()
    if expiry_datetime is not None and expiry_date is None:
        expiry_date = expiry_datetime.date()

    occ_ticker = option_format(
        symbol=underlying_ref.ticker,
        exp_date=expiry_date,
        flavor=callput,
        strike=strike,
    )

    if currency is None:
        if underlying_security.denominated_ccy is None:
            raise UnknownDenominatedCurrency(
                "Must declare denominated currency, if not supplied by underlier"
            )
        else:
            currency = underlying_security.denominated_ccy
    elif isinstance(currency, Security):
        currency = create_reference_from_security(currency)

    return Option(
        gsid=gsid,
        ticker=occ_ticker,
        strike=strike,
        option_flavor=flavor,
        security_type=SecurityType.DERIVATIVE,
        security_subtype=SecuritySubtype.EQUITY_OPTION,
        option_exercise=OptionExerciseStyle.AMERICAN,
        settlement_type=settlement_type,
        expiry_date=expiry_date,
        expiry_datetime=expiry_datetime,
        expiry_time_of_day=expiry_time_of_day,
        underlying=underlying_ref,
        multiplier=multiplier,
        denominated_ccy=currency,
        expiry_series_type=expiry_series_type,
        primary_exchange=primary_exc,
        identifiers=identifiers,
        website=website,
        issuer=None,
        **kwargs,
    )
