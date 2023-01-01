from .base import Security
from .enums import SecuritySubtype


def is_physical_settlement_available(security: Security) -> bool:
    # security_type = security.security_type
    security_subtype = security.security_subtype

    if security_subtype in (
        SecuritySubtype.DERIVED_INDEX,
        SecuritySubtype.UNKNOWN,
    ):
        return False
    else:
        return True
