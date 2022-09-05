import typing

import datetime
import math

__all__ = ['OCCSymbol','option_format','option_strike','option_flavor','option_maturity','option_symbol']

OCCSymbol = typing.NewType('OCCSymbol',str)


fmt1 = '%Y-%m-%d'
fmt2 = "%y%m%d"
    

def format_strike(strike):
    x = str(math.floor(float(strike) * 1000))
    return "0" * (8 - len(x)) + x


def option_format(
        symbol      : str,
        exp_date    : typing.Union[datetime.date, datetime.datetime, str],
        strike      : typing.Union[float,int],
        flavor      : typing.Literal['call','put'],
    ) -> OCCSymbol:
    """Returns the OCC standardized option name.
    Args:
            symbol: the underlying symbol, case insensitive
            exp_date: date of expiration, in string-form.
            strike: strike price of the option
            direction: 'C' or 'call' or the like, for call, otherwise 'p' or 'Put' for put
    Returns:
            OCC string, like 'IBM201231C00301000'
    .. code-block:: python
            # Construct the option's OCC symbol
            >>> ibm_call = option_format(
                    exp_date = '2020-12-31',
                    symbol = 'IBM', # case insensitive
                    direction = 'call',
                    strike = 301
            )
            >>> ibm_call
            'IBM201231C00301000'
    """

    if isinstance(exp_date, str):
        exp_date = datetime.datetime.strptime(exp_date,fmt1).date()
    
    assert( isinstance(exp_date, datetime.date) or isinstance(exp_date, datetime.datetime))

    # direction into C or P
    if flavor == 'call':
        d_char = 'C'
    elif flavor == 'put':
        d_char = 'P'

    symbol = str(symbol).strip().upper()

    # Assemble
    return '{symbol}{maturity}{d}{strike}'.format(
        symbol      = symbol,
        maturity    = exp_date.strftime(fmt2),
        d           =  d_char,
        strike      = format_strike(strike),
    )


def option_strike(name : OCCSymbol):
    """Pull apart an OCC standardized option name and
    retreive the strike price, in integer form"""
    return int(name[-8:]) / 1000.0


def option_maturity(name : OCCSymbol) -> datetime.date:
    """Given OCC standardized option name,
    return the date of maturity"""
    return datetime.datetime.strptime(name[-15:-9], fmt2).strftime(fmt1)


def option_flavor(name : OCCSymbol) -> typing.Literal['call','put']:
    """Given OCC standardized option name,
    return whether its a call or a put"""
    return "call" if name.upper()[-9] == "C" else "put"


def option_symbol(name : OCCSymbol) -> str:
    """Given OCC standardized option name, return option ticker"""
    return name[:-15]