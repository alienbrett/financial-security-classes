import typing
import dataclasses
import enum

import datetime

# import finsec as fs
from .classes import *
from .exceptions import *
from .exchanges import *


Ticker      = typing.NewType('Ticker', str)
GSID        = typing.NewType('GSID', typing.Any)

Currency    = float



@dataclasses.dataclass
class SecurityIdentifier:
    kind    : SecurityIdentifierType
    value   : str



@dataclasses.dataclass
class BaseSecurity:
    ### Application-level globally unique security id
    # Burden is on user to assign these in unique way,
    # if user chooses to use this
    gsid                : GSID

    #### The common ticker name
    # Different vendors may use different variations,
    #    but they'll be responsible for formatting correctly given this object
    ticker              : Ticker

    security_type       : SecurityType
    security_subtype    : SecuritySubtype
    identifiers         : typing.List[SecurityIdentifier]

    def __post_init__(self,):
        self.ticker = self.ticker.strip().upper()



@dataclasses.dataclass
class ListedSecurity(BaseSecurity):
    '''Security, but trades on an exchange
    '''
    primary_exchange    : typing.Optional[Exchange]



@dataclasses.dataclass
class IssuedInstrument:
    issuer              : typing.Optional[str]


@dataclasses.dataclass
class Currency(BaseSecurity, IssuedInstrument):
    pass



@dataclasses.dataclass
class Equity(ListedSecurity, IssuedInstrument):
    website             : typing.Optional[str]              = dataclasses.field(default='')
    description         : typing.Optional[str]              = dataclasses.field(default='')




@dataclasses.dataclass
class Derivative(ListedSecurity):

    settlement_type     : SettlementType
    expiry_series_type  : ExpirySeriesType
    expiry_time_of_day  : ExpiryTimeOfDay

    def __post_init__(self,):
        pass



@dataclasses.dataclass
class Option(Derivative):

    option_flavor   : OptionFlavor
    option_exercise : OptionExerciseStyle

    strike          : Currency


@dataclasses.dataclass
class Future(Derivative):
    pass
