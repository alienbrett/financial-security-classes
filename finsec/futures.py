import typing
from typing import Optional, List, Union

import datetime

from .base import *
from .enums import *
from .exchanges import *
from .exceptions import *
from .constructors import *
from .misc import *









def NewFuture (
        ticker              : Ticker,

        # Will link against this underlier
        underlying_security : Security,

        tick_size           : CurrencyQty,
        multiplier          : Multiplier,

        expiry_time_of_day  : ExpiryTimeOfDay,

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
    ) -> Future:


    description = None

    

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


    if currency is None:
        if underlying_security.denominated_ccy is None:
            raise UnknownDenominatedCurrencyException('Must declare denominated currency, if not supplied by underlier')
        else:
            currency = underlying_security.denominated_ccy
    elif isinstance(currency, Security):
            currency = create_reference_from_security( currency )


    return Future(
        ticker              = ticker,
        gsid                = gsid,

        underlying          = underlying_ref,

        tick_size           = tick_size,
        multiplier          = multiplier,

        security_type       = SecurityType.DERIVATIVE,
        security_subtype    = SecuritySubtype.FUTURE,

        settlement_type     = settlement_type,
        expiry_series_type  = expiry_series_type,
        expiry_time_of_day  = expiry_time_of_day,

        expiry_date         = expiry_date,
        expiry_datetime     = expiry_datetime,

        primary_exchange    = primary_exc,

        description         = description,
        identifiers         = identifiers,
        website             = website,
        issuer              = None,
        
        denominated_ccy     = currency,
    )

