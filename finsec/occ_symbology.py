import datetime
import math
import typing

OCCSymbol = typing.NewType("OCCSymbol", str)

fmt1 = "%Y-%m-%d"
fmt2 = "%y%m%d"


def format_strike(strike):
    x = str(math.floor(float(strike) * 1000))
    return "0" * (8 - len(x)) + x


def option_format(
    symbol: str,
    exp_date: typing.Union[datetime.date, datetime.datetime, str],
    strike: typing.Union[float, int],
    flavor: str,
) -> OCCSymbol:
    """Returns the OCC standardized option name.

    Args:
            symbol: the underlying symbol, case insensitive
            exp_date: date of expiration, in string-form.
            strike: strike price of the option
            flavor: 'C' or 'call' or the like, for call, otherwise 'p' or 'Put' for put
    Returns:
            OCC string, like 'IBM201231C00301000'
    """
    if isinstance(exp_date, str):
        exp_date = datetime.datetime.strptime(exp_date, fmt1).date()

    assert isinstance(exp_date, datetime.date) or isinstance(
        exp_date, datetime.datetime
    )

    if isinstance(flavor, str) and flavor[0].lower() in ("c", "p"):
        d_char = flavor[0].upper()
    else:
        raise ValueError(
            "Unknown option flavor of type {0} [{1}]".format(type(flavor), flavor)
        )

    symbol = str(symbol).strip().upper()

    return "{symbol}{maturity}{d}{strike}".format(
        symbol=symbol,
        maturity=exp_date.strftime(fmt2),
        d=d_char,
        strike=format_strike(strike),
    )


def option_strike(name: OCCSymbol):
    """Returns option strike from OCC standardized option name."""
    return int(name[-8:]) / 1000.0


def option_maturity(name: OCCSymbol) -> datetime.date:
    """Returns option maturity date from OCC standardized option name."""
    return datetime.datetime.strptime(name[-15:-9], fmt2).strftime(fmt1)


def option_flavor(name: OCCSymbol) -> str:
    """Returns option flavor ticker from OCC standardized option name.

    Return type should really be typing.Literal["call", "put"]
    """
    return "call" if name.upper()[-9] == "C" else "put"


def option_symbol(name: OCCSymbol) -> str:
    """Returns option underlying ticker from OCC standardized option name."""
    return name[:-15]
