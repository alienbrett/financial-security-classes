import enum


class Exchange(str, enum.Enum):
    UNKNOWN = "UNK"

    # USA
    NYSE = "NYS"
    NASDAQ = "NSQ"
    ARCA = "ARC"
    BATS = "BAT"
    IEX = "IEX"
    PHLX = "PHX"
    AMEX = "AMX"
    CME = "CME"
    CBOE = "CBO"

    # Canadian
    TORONTO = "TSX"
