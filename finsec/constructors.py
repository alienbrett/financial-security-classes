from typing import List, Optional

from .base import Security, SecurityIdentifier, SecurityReference
from .enums import GSID, SecurityIdentifierType, SecuritySubtype, SecurityType, Ticker
from .exceptions import MissingGSID
from .exchanges import Exchange


def Stock(
    ticker: Ticker,
    gsid: GSID = None,
    description: Optional[str] = None,
    website: Optional[str] = None,
    primary_exc: Optional[Exchange] = None,
    identifiers: Optional[List[SecurityIdentifier]] = None,
) -> Security:
    if identifiers is None:
        identifiers = []

    return Security(
        ticker=ticker,
        gsid=gsid,
        security_type=SecurityType.EQUITY,
        security_subtype=SecuritySubtype.COMMON_STOCK,
        primary_exchange=primary_exc,
        description=description,
        website=website,
        identifiers=identifiers,
        issuer=None,
        denominated_ccy=None,
    )


def ETP(
    ticker: Ticker,
    gsid: GSID = None,
    issuer: Optional[str] = None,
    description: Optional[str] = None,
    website: Optional[str] = None,
    primary_exc: Optional[Exchange] = None,
    identifiers: Optional[List[SecurityIdentifier]] = None,
) -> Security:
    if identifiers is None:
        identifiers = []

    return Security(
        ticker=ticker,
        gsid=gsid,
        security_type=SecurityType.EQUITY,
        security_subtype=SecuritySubtype.ETP,
        primary_exchange=primary_exc,
        description=description,
        website=website,
        identifiers=identifiers,
        issuer=(issuer if issuer is None else issuer.strip()),
        denominated_ccy=None,
    )


def FiatCurrency(
    ticker: Ticker,
    gsid: GSID = None,
    nation: str = None,
    description: Optional[str] = None,
    identifiers: Optional[List[SecurityIdentifier]] = None,
) -> Security:
    if identifiers is None:
        identifiers = []
    return Security(
        ticker=ticker,
        issuer=nation,
        gsid=gsid,
        security_type=SecurityType.CURRENCY,
        security_subtype=SecuritySubtype.NATIONAL_FIAT,
        identifiers=identifiers,
        primary_exchange=None,
        website=None,
        description=description,
        denominated_ccy=None,
    )


def CryptoCurrency(
    ticker: Ticker,
    gsid: GSID = None,
    description: Optional[str] = None,
    identifiers: Optional[List[SecurityIdentifier]] = None,
) -> Security:
    if identifiers is None:
        identifiers = []

    return Security(
        ticker=ticker,
        issuer=None,
        gsid=gsid,
        security_type=SecurityType.CURRENCY,
        security_subtype=SecuritySubtype.CRYPTOCURRENCY,
        identifiers=identifiers,
        primary_exchange=None,
        website=None,
        description=description,
        denominated_ccy=None,
    )


def DerivedIndex(
    ticker: Ticker,
    gsid: GSID = None,
    website: Optional[str] = None,
    issuer: Optional[str] = None,
    description: Optional[str] = None,
    currency: Optional[Security] = None,
    identifiers: Optional[List[SecurityIdentifier]] = None,
) -> Security:
    if identifiers is None:
        identifiers = []

    if currency is not None:
        currency_ref = create_reference_from_security(currency)
    else:
        currency_ref = None

    return Security(
        ticker=ticker,
        gsid=gsid,
        security_type=SecurityType.INDEX,
        security_subtype=SecuritySubtype.DERIVED_INDEX,
        issuer=issuer,
        website=website,
        identifiers=identifiers,
        primary_exchange=None,
        description=description,
        denominated_ccy=currency_ref,
    )


def FIGI(value: str) -> SecurityIdentifier:
    return SecurityIdentifier(id_type=SecurityIdentifierType.FIGI, value=value)


def ISIN(value: str) -> SecurityIdentifier:
    return SecurityIdentifier(id_type=SecurityIdentifierType.ISIN, value=value)


def CUSIP(value: str) -> SecurityIdentifier:
    return SecurityIdentifier(id_type=SecurityIdentifierType.CUSIP, value=value)


def create_reference_from_security(security: Security) -> SecurityReference:
    if security.gsid is None:
        raise MissingGSID("security gsid not provided")
    return SecurityReference(
        gsid=security.gsid,
        ticker=security.ticker,
        security_type=security.security_type,
        security_subtype=security.security_subtype,
    )
