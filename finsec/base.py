import typing
import dataclasses


from .enums import *
from .exceptions import *
from .exchanges import *



@dataclasses.dataclass
class SecurityIdentifier:
    kind    : SecurityIdentifierType
    value   : str



@dataclasses.dataclass
class Security:
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

    primary_exchange    : typing.Optional[Exchange]

    issuer              : typing.Optional[str]
    description         : typing.Optional[str]
    website             : typing.Optional[str]

    def __post_init__(self,):
        self.ticker = self.ticker.strip().upper()





@dataclasses.dataclass
class Derivative(Security):

    underlying          : Ticker

    settlement_type     : SettlementType
    expiry_series_type  : ExpirySeriesType
    expiry_time_of_day  : ExpiryTimeOfDay

    def __post_init__(self,):
        pass



@dataclasses.dataclass
class Option(Derivative):

    option_flavor   : OptionFlavor
    option_exercise : OptionExerciseStyle

    strike          : CurrencyQty


@dataclasses.dataclass
class Future(Derivative):
    pass
