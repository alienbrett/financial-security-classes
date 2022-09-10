### Test optional dependencies
# Strawberry #
try:
    import strawberry
    strawberry_enabled = True
except:
    strawberry_enabled = False
# print('Strawberry enabled: {0}'.format(str(strawberry_enabled)))

# Pydantic #
try:
    from pydantic.dataclasses import dataclass
    pydantic_enabled = True
except:
    from dataclasses import dataclass
    pydantic_enabled = False
# print('pydantic enabled: {0}'.format(str(pydantic_enabled)))


####################
import typing
import dataclasses
import datetime
from dataclasses_json import dataclass_json

from .enums         import *
from .exceptions    import *
from .exchanges     import *
from .config        import *


placeholder = lambda: dataclasses.field(default=False)



@dataclass_json
@dataclass
class SecurityIdentifier:
    id_type : SecurityIdentifierType
    value   : str

if strawberry_enabled:
    SecurityIdentifier = strawberry.type()(SecurityIdentifier)



@dataclass_json
@dataclass
class SecurityReference:
    gsid                : GSID
    ticker              : Ticker

if strawberry_enabled:
    SecurityReference = strawberry.type()(SecurityReference)



@dataclass_json
@dataclass
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

    #### Security data valid and recent as-of this data
    as_of_date         : typing.Optional[datetime.datetime] \
        = dataclasses.field(metadata=maybe_datetime_field_config, default=None)

    def __post_init__(self,):
        self.ticker = self.ticker.strip().upper()

if strawberry_enabled:
    Security = strawberry.type()(Security)



@dataclass_json
@dataclass
class Derivative(Security):

    ### Underlying that determines settlement of the contract
    underlying          : SecurityReference = placeholder()

    settlement_type     : SettlementType = placeholder()
    expiry_series_type  : ExpirySeriesType = placeholder()
    expiry_time_of_day  : ExpiryTimeOfDay = placeholder()

    expiry_date         : datetime.date \
        = dataclasses.field(metadata=date_field_config, default=None)
    expiry_datetime     : typing.Optional[datetime.datetime] \
        = dataclasses.field(metadata=maybe_datetime_field_config, default=None)

    ####### The multiplier vs underlier
    multiplier          : Multiplier = placeholder()

if strawberry_enabled:
    Derivative = strawberry.type()(Derivative)


@dataclass_json
@dataclass
class Future(Derivative):
    ####### The minimum tick sizerement
    tick_size           : CurrencyQty = placeholder()

if strawberry_enabled:
    Future = strawberry.type()(Future)


@dataclass_json
@dataclass
class Option(Derivative):

    option_flavor   : OptionFlavor = placeholder()
    option_exercise : OptionExerciseStyle = placeholder()

    strike          : CurrencyQty = placeholder()

if strawberry_enabled:
    Option = strawberry.type()(Option)



