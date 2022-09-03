import typing
import enum



Ticker          = typing.NewType('Ticker', str)
GSID            = typing.NewType('GSID', typing.Any)

CurrencyQty     = float
Multiplier      = float




class SecurityType(enum.Enum):
    UNKNOWN             = 0

    COMMODITY           = 1
    CURRENCY            = 2
    DEBT                = 3
    EQUITY              = 4
    DERIVATIVE          = 5
    ALTERNATIVE         = 6
    INDEX               = 7
    STRUCTURE           = 10
    BASKET              = 12




class SecuritySubtype(enum.Enum):
    '''Generics must value divisible by 100, and visa-versa
    '''
    ##### Reserved 0-999
    UNKNOWN             = 0
    DERIVED_INDEX       = 10

    
    SOFT_COMMODITY      = 110
    ENERGY              = 115
    METAL               = 120
    GRAIN               = 125
    LIVESTOCK           = 130

    ##### Currencies
    NATIONAL_FIAT       = 505
    CRYPTOCURRENCY      = 510

    ##### Equity 1000-2000
    COMMON_STOCK        = 1005
    PREFERRED_STOCK     = 1010
    ETP                 = 1020

    ######## Equity Derivatives

    ### Futures
    FUTURE              = 2001
    SINGLE_STOCK_FUTURE = 2002
    PERPETUAL_FUTURE    = 2003



    ### Calls end in 2, puts end in 1 (x % 10)
    EQUITY_OPTION       = 2005
    # SWAPTION            = 20


    ##### Structures (fits, and whatnot)
    # like LIBOR cash, or US treasury cash
    # rates curve quotes will reference an underlyer like this






class SettlementType(enum.Enum):
    UNKNOWN     = 0

    CASH        = 1
    PHYSICAL    = 2



class SecurityIdentifierType(enum.Enum):
    UNKNOWN     = 0

    FIGI        = 2
    ISIN        = 3
    CUSIP       = 4
    OCC         = 5



class OptionFlavor(enum.Enum):
    UNKNOWN     = 0

    PUT         = 1
    CALL        = 2



class OptionExerciseStyle(enum.Enum):
    UNKNOWN     = 0
    #### Exercise only possible at expiration
    EUROPEAN    = 1

    #### Expiry possible any day up until and including expiration
    AMERICAN    = 2

    #### Expiry possible on a subset of days prior to, and including expiration
    # BERMUDAN    = 3




class ExpirySeriesType(enum.Enum):
    UNKNOWN     = 0

    QUARTERLY   = 10
    MONTHLY     = 20
    WEEKLY      = 30




class ExpiryTimeOfDay(enum.Enum):
    UNKOWN      = 0

    OPEN        = 1
    EDSP        = 2
    CLOSE       = 3
