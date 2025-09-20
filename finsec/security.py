import datetime
import decimal
import uuid
from typing import Any, Dict, List, Optional, Union

import bson
import numpy as np
import pandas as pd
import pydantic

from .base import Derivative, Future, Option, Security
from .enums import (
    GSID,
    CurrencyQty,
    ExpirySeriesType,
    ExpiryTimeOfDay,
    Multiplier,
    OptionExerciseStyle,
    OptionFlavor,
    SecurityIdentifierType,
    SecuritySubtype,
    SecurityType,
    SettlementType,
    Ticker,
)
from .exchanges import Exchange
from .fixed_income import Bond, Cashflow, FixedLeg, FloatingLeg, Swap
from .format import pretty_print_security
from .utils import format_number, placeholder

AnySecurity = Union[
    Option,
    Future,
    Security,
    Derivative,
    # FixingIndex,
    Cashflow,
    FixedLeg,
    FloatingLeg,
    Swap,
    Bond,
]
