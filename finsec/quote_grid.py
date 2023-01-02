from typing import Any, Callable, Dict, List, Optional, Union

import pydantic

from .base import GSID, Security, SecurityReference
from .constructors import create_reference_from_security

# from .enums import *
# from .exceptions import
# from .exchanges import Exchange
from .quotes import AbstractQuote

# from .utils import *


SecurityLookupKey = Union[GSID, Security, SecurityReference]


def as_gsid(k: SecurityLookupKey) -> GSID:
    if isinstance(k, Security):
        k = create_reference_from_security(k)
    if isinstance(k, SecurityReference):
        k = k.gsid
    return k


class SecurityCache(pydantic.BaseModel):
    """Caches securities against GSID, and operates kinda like a dict."""

    securities: Dict[GSID, Security] = {}

    def __getitem__(self, k: SecurityLookupKey) -> Optional[Security]:
        return self.securities.__getitem__(as_gsid(k))

    def __setitem__(self, k: SecurityLookupKey, v: Security):
        return self.securities.__setitem__(as_gsid(k), v)

    def __delitem__(self, k: Union[SecurityLookupKey, Security, SecurityReference]):
        return self.securities.__delitem__(as_gsid(k))

    def __contains__(self, k: SecurityLookupKey):
        k = as_gsid(k)
        return k in self.securities

    def __iter__(self):
        return list(self.securities.values()).__iter__()

    def add(self, sec: Security):
        self.__setitem__(sec.gsid, sec)
        return sec.gsid


class QuoteGrid(pydantic.BaseModel):
    """Stores quotes and securities against GSIDs. Helps quickly can quickly perform business logic without re-buildling securities and qutoes."""

    quotes: Dict[GSID, AbstractQuote] = pydantic.Field(default_factory=dict)
    sec_cache: SecurityCache = pydantic.Field(default_factory=SecurityCache)

    def ingest(self, sec: Security, quote: AbstractQuote):
        """Incorporates a security and quote into the object."""
        if isinstance(sec, Security):
            sec_gsid = self.sec_cache.add(sec)
        else:
            sec_gsid = sec

        self.quotes[sec_gsid] = quote

    def __getitem__(self, k: SecurityLookupKey) -> Optional[Security]:
        return self.quotes.__getitem__(as_gsid(k))

    def __setitem__(self, k: SecurityLookupKey, v: Security):
        return self.quotes.__setitem__(as_gsid(k), v)

    def __delitem__(self, k: Union[SecurityLookupKey, Security, SecurityReference]):
        return self.quotes.__delitem__(as_gsid(k))

    def __contains__(self, k: SecurityLookupKey):
        k = as_gsid(k)
        return k in self.quotes


class SecurityChain(QuoteGrid, pydantic.BaseModel):
    """Stores derivatives and their quotes against GSIDs. Helps quickly can quickly perform business logic without re-buildling securities and qutoes."""

    underlying: Optional[Security] = None

    def get_available_values(self, attr: str) -> List[Any]:
        """Searches all securities in this chain, and returns list of the unique attribute values for specified attribute."""
        return list({getattr(sec, attr) for sec in self.sec_cache})

    def filter(self, func: Callable[[Security], bool]):
        """Returns generator that yields all securities matching some criteria function."""
        for sec in filter(func, self.sec_cache):
            yield sec

    def subset(self, **kwargs):
        """Iterates through all securities with attributes matching the kwargs specified."""

        def match_func(sec: Security) -> bool:
            return all(v == getattr(sec, k) for k, v in kwargs.items())

        return self.filter(match_func)


class FutureChain(SecurityChain, pydantic.BaseModel):
    pass


class OptionChain(SecurityChain, pydantic.BaseModel):
    pass


class FutureOptionChain(SecurityChain, pydantic.BaseModel):
    pass
