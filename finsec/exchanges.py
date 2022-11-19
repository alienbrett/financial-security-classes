# try:
#     import strawberry
#     strawberry_enabled = True
# except:
#     strawberry_enabled = False

import enum


class Exchange(str, enum.Enum):
    UNKNOWN     = 'UNK'

    ### USA
    NYSE        = 'NYS'
    NASDAQ      = 'NSQ'
    ARCA        = 'ARC'
    BATS        = 'BAT'
    IEX         = 'IEX'
    PHLX        = 'PHX'
    AMEX        = 'AMX'
    CME         = 'CME'
    CBOE        = 'CBO'


    ### Canadian
    TORONTO     = 'TSX'
# if strawberry_enabled:
#     Exchange = strawberry.type()(Exchange)
