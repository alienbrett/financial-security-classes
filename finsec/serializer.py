import json
import logging
from typing import Any, Callable, Dict, Optional

log = logging.getLogger(__name__)


from .base import Derivative, Future, Option, Security
from .enums import SecuritySubtype, SecurityType, future_subtypes, option_subtypes


def get_constructor_from_types(
    security_type: SecurityType, security_subtype: SecuritySubtype
) -> Callable[..., Security]:
    """Returns the constructor which builds a security from a dict of kwargs."""
    result = Security

    if security_type in (SecurityType.DERIVATIVE,):
        if security_subtype in option_subtypes:
            result = Option
        elif security_subtype in future_subtypes:
            result = Future
        else:
            # Maybe this should be an assertion error...
            # This case should never execute
            result = Derivative

    else:
        # This case will need to be expanded as more security types are fleshed out
        pass

    log.debug(
        "security constructor for {0}.{1}\t=> {2}".format(
            security_type,
            security_subtype,
            result,
        )
    )
    return result


def get_constructor(obj_dict: Dict[Any, Any]) -> Optional[Callable[..., Security]]:
    """Infers the necessary constructor from the dict provided, and returns that constructor."""
    security_type = SecurityType(obj_dict["security_type"])
    security_subtype = SecuritySubtype(obj_dict["security_subtype"])
    return get_constructor_from_types(security_type, security_subtype)


def dict_encode(security: Security) -> Dict:
    """Converts security into dict."""
    res = security.dict()
    res = {k: v for k, v in res.items() if v is not None}
    return res


def dict_decode(obj_dict: Dict[Any, Any]) -> Security:
    """Converts dict into a security."""
    constructor = get_constructor(obj_dict)
    return constructor(**obj_dict)


def json_encode(security: Security) -> str:
    """Converts security into json string."""
    res = security.json()
    return res


def json_decode(obj_json: str) -> Security:
    """Converts json string into a security."""
    obj_dict = json.loads(obj_json)
    return get_constructor(obj_dict)(**obj_dict)
