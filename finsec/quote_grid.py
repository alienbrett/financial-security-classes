import pydantic
# import dataclasses
from typing import *
import enum

import datetime

from .base import *
from .enums import *
from .exchanges import *
from .exceptions import *
from .constructors import *
from .quotes import *
from .utils import *



class SecurityCache(pydantic.BaseModel):
    securities  : Dict[GSID, Security] = {}

    def __getitem__(self, k: GSID) -> Optional[Security]:
        return self.securities.__getitem__(k)

    def __setitem__(self, k: GSID, v: Security):
        return self.securities.__setitem__(k, v)
    
    def __delitem__(self, k: GSID):
        return self.securities.__delitem__(k)

    def __contains__(self, k: GSID):
        return k in self.securities
    
    def __iter__(self):
        return list(self.securities.values()).__iter__()


    def add(self, sec : Security):
        # print('adding security to cache')
        self.__setitem__(sec.gsid, sec)
        # print(self.securities)
        return sec.gsid





class QuoteGrid(pydantic.BaseModel):
    quotes      : Dict[ GSID, AbstractQuote ]   = pydantic.Field( default_factory = dict )
    sec_cache   : SecurityCache                 = pydantic.Field( default_factory = SecurityCache )

    def ingest(self, sec : Union[Security, GSID], quote : AbstractQuote):
        if isinstance(sec, Security):
            sec_gsid = self.sec_cache.add(sec)
        else:
            sec_gsid = sec


        self.quotes[sec_gsid] = quote


class SecurityChain(QuoteGrid, pydantic.BaseModel):
    underlying  : Optional[Security] = None


    def get_available_values(self, attr : str) -> List[Any]:
        '''Searches all securities in this chain, and returns list of the unique attribute values for specified attribute
        '''
        return list(set( getattr(sec, attr) for sec in self.sec_cache ))


    def subset(self, **kwargs):
        '''Iterates through all securities with attributes matching what was passed in
        '''
        def match_func(sec: Security) -> bool:
            return all( v == getattr(sec, k) for k,v in kwargs.items() )

        for sec in filter(match_func, self.sec_cache):
            yield sec




class FutureChain(SecurityChain, pydantic.BaseModel):
    pass


class OptionChain(SecurityChain, pydantic.BaseModel):
    pass


class FutureOptionChain(SecurityChain, pydantic.BaseModel):
    pass