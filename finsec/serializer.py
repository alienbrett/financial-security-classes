import typing

import json
from dataclasses_json import dataclass_json


from .base          import *
from .enums         import *
from .exceptions    import *


def get_constructor_from_types(security_type : SecurityType, security_subtype : SecuritySubtype):
    if security_type in (
            SecurityType.DERIVATIVE,
        ):
        if security_subtype in (SecuritySubtype.EQUITY_OPTION,):
            return Option
        elif security_subtype in (SecuritySubtype.FUTURE,):
            return Future
        else:
            ## Maybe this should be an assertion error...
            # This case should never execute
            return Derivative
    
    else:
        ### This case will need to be expanded as more security types are fleshed out
        return Security


def get_constructor( obj_dict ):
    security_type       = SecurityType(obj_dict['security_type'])
    security_subtype    = SecuritySubtype(obj_dict['security_subtype'])
    return get_constructor_from_types(security_type, security_subtype)


##############

def dict_encode( security : Security ) -> typing.Dict:
    return security.to_dict()

def dict_decode( obj_dict ) -> Security:
    constructor = get_constructor(obj_dict)
    # print(constructor, obj_dict, )
    return constructor.from_dict(obj_dict)

def json_encode( security : Security ) -> str:
    return security.to_json()

def json_decode( obj_json ) -> Security:
    obj_dict = json.loads( obj_json )
    return get_constructor(obj_dict).from_dict(obj_dict)


