from asyncio import create_subprocess_exec
import typing
from typing import Optional, List, Union

import dataclasses
import enum

import datetime

from .base import *
from .enums import *
from .exchanges import *
from .exceptions import *
from .constructors import *
from .occ_symbology import *
from .utils import *









def European (
        # Will link against this underlier
        underlying_security : Security,

        multiplier          : Multiplier,

        expiry_time_of_day  : ExpiryTimeOfDay,

        strike              : CurrencyQty,
        
        ## Callput should be in ('call','put')
        callput             : str,

        expiry_date         : datetime.date,
        expiry_datetime     : Optional[datetime.datetime]   = None,

        ### If underlier is an index, then settlement inferred as cash-settled
        settlement_type     : Optional[SettlementType]      = None,

        ### If none, this is set to UNKNOWN
        expiry_series_type  : Optional[ExpirySeriesType]    = None,

        primary_exc         : Optional[Exchange]            = None,
        website             : Optional[str]                 = None,
        identifiers         : List[SecurityIdentifier]      = [],

        gsid                : GSID                          = None,

        ### Currency will be used, if it cannot be inferred from underlying
        currency            : Union[Security,SecurityReference,None] = None,
    ) -> Option:
    description = None

    good_callput = callput.strip().lower()
    if good_callput == 'call':
        flavor = OptionFlavor.CALL
    elif good_callput == 'put':
        flavor = OptionFlavor.PUT
    else:
        raise ValueError('Unknown callput type: {0}'.format(callput))

    if is_physical_settlement_available( underlying_security ):
        if settlement_type is None:
            raise InvalidSettlementTypeException('Must specify settlement type, since underlying permits physical delivery')
    else:

        if settlement_type == SettlementType.PHYSICAL:
            raise InvalidSettlementTypeException('Cannot physically-settle a derived index')
        else:
            settlement_type = SettlementType.CASH
        
    if expiry_series_type is None:
        expiry_series_type = ExpirySeriesType.UNKNOWN

    underlying_ref = create_reference_from_security( underlying_security )

    if isinstance(expiry_date, str):
        expiry_date = datetime.datetime.strptime(expiry_date, '%Y-%m-%d').date()
    if expiry_datetime is not None and expiry_date is None:
        expiry_date = expiry_datetime.date()

    occ_ticker = option_format(
        symbol      = underlying_ref.ticker,
        exp_date    = expiry_date,
        flavor      = callput,
        strike      = strike,
    )

    if currency is None:
        if underlying_security.denominated_ccy is None:
            raise UnknownDenominatedCurrencyException('Must declare denominated currency, if not supplied by underlier')
        else:
            currency = underlying_security.denominated_ccy
    elif isinstance(currency, Security):
            currency = create_reference_from_security( currency )

    return Option(
        gsid                = gsid,
        ticker              = occ_ticker,
        strike              = strike,
        option_flavor       = flavor,

        security_type       = SecurityType.DERIVATIVE,
        security_subtype    = SecuritySubtype.EQUITY_OPTION,

        option_exercise     = OptionExerciseStyle.EUROPEAN,
        settlement_type     = settlement_type,
        expiry_date         = expiry_date,
        expiry_datetime     = expiry_datetime,
        expiry_time_of_day  = expiry_time_of_day,
        underlying          = underlying_ref,

        multiplier          = multiplier,
        denominated_ccy     = currency,
        expiry_series_type  = expiry_series_type,

        primary_exchange    = primary_exc,

        description         = description,
        identifiers         = identifiers,
        website             = website,
        issuer              = None,
    )





def American (
        # Will link against this underlier
        underlying_security : Security,

        multiplier          : Multiplier,

        expiry_time_of_day  : ExpiryTimeOfDay,

        strike              : CurrencyQty,
        
        ## Callput should be in ('call','put')
        callput             : str,

        expiry_date         : datetime.date,
        expiry_datetime     : Optional[datetime.datetime]   = None,

        ### If underlier is an index, then settlement inferred as cash-settled
        settlement_type     : Optional[SettlementType]      = None,

        ### If none, this is set to UNKNOWN
        expiry_series_type  : Optional[ExpirySeriesType]    = None,

        primary_exc         : Optional[Exchange]            = None,
        website             : Optional[str]                 = None,
        identifiers         : List[SecurityIdentifier]      = [],

        gsid                : GSID                          = None,

        ### Currency will be used, if it cannot be inferred from underlying
        currency            : Union[Security,SecurityReference,None] = None,
    ) -> Option:
    description = None

    good_callput = callput.strip().lower()
    if good_callput == 'call':
        flavor = OptionFlavor.CALL
    elif good_callput == 'put':
        flavor = OptionFlavor.PUT
    else:
        raise ValueError('Unknown callput type: {0}'.format(callput))

    if is_physical_settlement_available( underlying_security ):
        if settlement_type is None:
            raise InvalidSettlementTypeException('Must specify settlement type, since underlying permits physical delivery')
    else:

        if settlement_type == SettlementType.PHYSICAL:
            raise InvalidSettlementTypeException('Cannot physically-settle a derived index')
        else:
            settlement_type = SettlementType.CASH
        
    if expiry_series_type is None:
        expiry_series_type = ExpirySeriesType.UNKNOWN

    underlying_ref = create_reference_from_security( underlying_security )

    if isinstance(expiry_date, str):
        expiry_date = datetime.datetime.strptime(expiry_date, '%Y-%m-%d').date()
    if expiry_datetime is not None and expiry_date is None:
        expiry_date = expiry_datetime.date()

    occ_ticker = option_format(
        symbol      = underlying_ref.ticker,
        exp_date    = expiry_date,
        flavor      = callput,
        strike      = strike,
    )

    if currency is None:
        if underlying_security.denominated_ccy is None:
            raise UnknownDenominatedCurrencyException('Must declare denominated currency, if not supplied by underlier')
        else:
            currency = underlying_security.denominated_ccy
    elif isinstance(currency, Security):
            currency = create_reference_from_security( currency )

    return Option(
        gsid                = gsid,
        ticker              = occ_ticker,
        strike              = strike,
        option_flavor       = flavor,

        security_type       = SecurityType.DERIVATIVE,
        security_subtype    = SecuritySubtype.EQUITY_OPTION,

        option_exercise     = OptionExerciseStyle.AMERICAN,
        settlement_type     = settlement_type,
        expiry_date         = expiry_date,
        expiry_datetime     = expiry_datetime,
        expiry_time_of_day  = expiry_time_of_day,
        underlying          = underlying_ref,

        multiplier          = multiplier,
        denominated_ccy     = currency,
        expiry_series_type  = expiry_series_type,

        primary_exchange    = primary_exc,

        description         = description,
        identifiers         = identifiers,
        website             = website,
        issuer              = None,
    )
