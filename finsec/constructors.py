import typing
import dataclasses
import enum

import datetime

# import finsec as fs
from .base import *
from .classes import *
from .exchanges import *
from .exceptions import *


def Stock (
        ticker      : Ticker,
        gsid        : GSID                              = None,
        description : typing.Optional[str]              = None,
        website     : typing.Optional[str]              = None,
        primary_exc : typing.Optional[Exchange]         = None,
        identifiers : typing.List[SecurityIdentifier]   = [],
    ) -> Equity:

    return Equity(
        ticker          = ticker,
        gsid            = gsid,
        security_type   = SecurityType.EQUITY,
        security_subtype= SecuritySubtype.COMMON_STOCK,
        primary_exchange= primary_exc,
        description     = description,
        website         = website,
        identifiers     = identifiers,
        issuer          = None,
    )


def ETP (
        ticker      : Ticker,
        gsid        : GSID                              = None,
        issuer      : typing.Optional[str]              = None,
        description : typing.Optional[str]              = None,
        website     : typing.Optional[str]              = None,
        primary_exc : typing.Optional[Exchange]         = None,
        identifiers : typing.List[SecurityIdentifier]   = [],
    ) -> Equity:

    return Equity(
        ticker          = ticker,
        gsid            = gsid,
        security_type   = SecurityType.EQUITY,
        security_subtype= SecuritySubtype.ETP,
        primary_exchange= primary_exc,
        description     = description,
        website         = website,
        identifiers     = identifiers,
        issuer          = (issuer if issuer is None else issuer.strip()),
    )



def FiatCurrency(
        ticker      : Ticker,
        gsid        : GSID                  = None,
        nation      : str                   = None,
        identifiers : typing.List[SecurityIdentifier]   = [],
    ) -> Currency:
    return Currency(
        ticker          = ticker,
        issuer          = nation,
        gsid            = gsid,
        security_type   = SecurityType.CURRENCY,
        security_subtype= SecuritySubtype.NATIONAL_FIAT,
        identifiers     = identifiers,
    )




def CryptoCurrency(
        ticker      : Ticker,
        gsid        : GSID                  = None,
        identifiers : typing.List[SecurityIdentifier]   = [],
    ) -> Currency:
    return Currency(
        ticker          = ticker,
        issuer          = None,
        gsid            = gsid,
        security_type   = SecurityType.CURRENCY,
        security_subtype= SecuritySubtype.CRYPTOCURRENCY,
        identifiers     = identifiers,
    )







def FIGI(value : str) -> SecurityIdentifier:
    return SecurityIdentifier(kind=SecurityIdentifierType.FIGI, value=value)

def ISIN(value : str) -> SecurityIdentifier:
    return SecurityIdentifier(kind=SecurityIdentifierType.ISIN, value=value)

def CUSIP(value : str) -> SecurityIdentifier:
    return SecurityIdentifier(kind=SecurityIdentifierType.CUSIP, value=value)