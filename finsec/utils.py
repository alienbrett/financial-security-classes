# import finsec as fs
from .base import *
from .enums import *
from .exchanges import *
from .exceptions import *
from .constructors import *

def is_physical_settlement_available(security : Security) -> bool:
    security_type = security.security_type 
    security_subtype = security.security_subtype 

    if security_subtype in (
        SecuritySubtype.DERIVED_INDEX,
        SecuritySubtype.UNKNOWN,
    ):
        return False
    else:
        return True
