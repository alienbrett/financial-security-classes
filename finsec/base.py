import typing
import dataclasses
import datetime


from .enums import *
from .exceptions import *
from .exchanges import *



@dataclasses.dataclass
class SecurityIdentifier:
    kind    : SecurityIdentifierType
    value   : str


@dataclasses.dataclass
class SecurityReference:
    gsid                : GSID
    ticker              : Ticker


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

    denominated_ccy     : typing.Optional[SecurityReference]

    issuer              : typing.Optional[str]
    description         : typing.Optional[str]
    website             : typing.Optional[str]


    def __post_init__(self,):
        self.ticker = self.ticker.strip().upper()




@dataclasses.dataclass
class Derivative(Security):

    ### Underlying that determines settlement of the contract
    underlying          : SecurityReference

    settlement_type     : SettlementType
    expiry_series_type  : ExpirySeriesType
    expiry_time_of_day  : ExpiryTimeOfDay

    expiry_date         : datetime.date
    expiry_datetime     : typing.Optional[datetime.datetime]

    ####### The multiplier vs underlier
    multiplier          : Multiplier



@dataclasses.dataclass
class Future(Derivative):
    ####### The minimum tick sizerement
    tick_size           : CurrencyQty


@dataclasses.dataclass
class Option(Derivative):

    option_flavor   : OptionFlavor
    option_exercise : OptionExerciseStyle

    strike          : CurrencyQty


