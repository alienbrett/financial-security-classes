import decimal
import enum
import typing

Ticker = typing.NewType("Ticker", str)
GSID = typing.NewType("GSID", typing.Any)
CurrencyQty = typing.NewType("CurrencyQty", decimal.Decimal)
Multiplier = typing.NewType("Multiplier", decimal.Decimal)
Size = typing.NewType("Size", decimal.Decimal)


class SecurityType(int, enum.Enum):
    UNKNOWN = 0

    COMMODITY = 1
    CURRENCY = 2
    DEBT = 3
    EQUITY = 4
    DERIVATIVE = 5
    ALTERNATIVE = 6
    INDEX = 7
    STRUCTURE = 10
    BASKET = 12


class SecuritySubtype(int, enum.Enum):

    # Reserved 0-999
    UNKNOWN = 0
    DERIVED_INDEX = 10
    OVERNIGHT_RATE = 80
    TERM_RATE = 85

    SOFT_COMMODITY = 110
    ENERGY = 115
    METAL = 120
    GRAIN = 125
    LIVESTOCK = 130

    # Currencies
    NATIONAL_FIAT = 505
    CRYPTOCURRENCY = 510

    # Equity 1000-2000
    COMMON_STOCK = 1005
    PREFERRED_STOCK = 1010
    ETP = 1020

    # Equity Derivatives

    # Futures
    FUTURE = 2001
    SINGLE_STOCK_FUTURE = 2002
    PERPETUAL_FUTURE = 2003
    FORWARD = 2010

    INDEX_OPTION = 2030
    EQUITY_OPTION = 2040
    CURRENCY_OPTION = 2050


class SettlementType(int, enum.Enum):
    UNKNOWN = 0
    CASH = 1
    PHYSICAL = 2


class SecurityIdentifierType(int, enum.Enum):
    UNKNOWN = 0
    FIGI = 2
    ISIN = 3
    CUSIP = 4
    OCC = 5


class OptionFlavor(int, enum.Enum):
    UNKNOWN = 0
    PUT = 1
    CALL = 2


class OptionExerciseStyle(int, enum.Enum):
    UNKNOWN = 0
    EUROPEAN = 1
    AMERICAN = 2
    BERMUDAN = 3


class ExpirySeriesType(int, enum.Enum):
    UNKNOWN = 0
    QUARTERLY = 10
    MONTHLY = 20
    WEEKLY = 30


class ExpiryTimeOfDay(int, enum.Enum):
    UNKNOWN = 0
    OPEN = 1
    EDSP = 2
    CLOSE = 3


option_subtypes = (
    SecuritySubtype.EQUITY_OPTION,
    SecuritySubtype.INDEX_OPTION,
    SecuritySubtype.CURRENCY_OPTION,
)

future_subtypes = (
    SecuritySubtype.FUTURE,
    SecuritySubtype.SINGLE_STOCK_FUTURE,
    SecuritySubtype.PERPETUAL_FUTURE,
    SecuritySubtype.FORWARD,
)
