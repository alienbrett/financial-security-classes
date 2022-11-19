import logging
log = logging.getLogger(__name__)

import typing
import json

from .base          import *
from .enums         import *
from .exceptions    import *


def get_constructor_from_types(security_type : SecurityType, security_subtype : SecuritySubtype):

    result = Security

    if security_type in (
            SecurityType.DERIVATIVE,
        ):
        if security_subtype in (SecuritySubtype.EQUITY_OPTION,):
            result = Option
        elif security_subtype in (SecuritySubtype.FUTURE,):
            result = Future
        else:
            ## Maybe this should be an assertion error...
            # This case should never execute
            result = Derivative
    
    else:
        ### This case will need to be expanded as more security types are fleshed out
        pass

    log.info('security constructor for {0}.{1}\t=> {2}'.format(
        security_type,
        security_subtype,
        result,
    ))
    return result


def get_constructor( obj_dict ):
    security_type       = SecurityType(obj_dict['security_type'])
    security_subtype    = SecuritySubtype(obj_dict['security_subtype'])
    return get_constructor_from_types(security_type, security_subtype)


##############

def dict_encode( security : Security ) -> typing.Dict:
    return security.dict()

def dict_decode( obj_dict ) -> Security:
    constructor = get_constructor(obj_dict)
    return constructor(**obj_dict)

def json_encode( security : Security ) -> str:
    res = security.json()
    return res


def json_decode( obj_json ) -> Security:
    obj_dict = json.loads( obj_json )
    return get_constructor(obj_dict)(**obj_dict)


