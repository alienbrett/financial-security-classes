from time import CLOCK_BOOTTIME
# import typing
# import dataclasses
import enum


class Exchange(enum.Enum):
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

