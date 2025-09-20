import datetime
import decimal
from typing import Any, List, Optional, Union, Dict

import pandas as pd
import numpy as np
import pydantic
import bson
import uuid

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
from .utils import placeholder, format_number
from .format import pretty_print_security

from .base import (
    Option,
    Future,
    Security,
    Derivative,
)

from .fixed_income import (
    Cashflow,
    FixedLeg,
    FloatingLeg,
    Swap,
    Bond,
)

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
