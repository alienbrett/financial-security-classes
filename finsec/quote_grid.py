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

    def __len__(self):
        return len(self.securities)

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

    def add(self, sec: Security, overwrite: bool = False):
        if not ((not overwrite) and (sec.gsid in self.securities)):
            self.__setitem__(sec.gsid, sec)
        return sec.gsid


class QuoteGrid(pydantic.BaseModel):
    """Stores quotes and securities against GSIDs. Helps quickly can quickly perform business logic without re-buildling securities and qutoes."""

    quotes: Dict[GSID, AbstractQuote] = pydantic.Field(default_factory=dict)
    sec_cache: SecurityCache = pydantic.Field(default_factory=SecurityCache)

    def ingest(self, sec: Security, quote: AbstractQuote, overwrite: bool = False):
        """Incorporates a security and quote into the object."""
        if isinstance(sec, Security):
            sec_gsid = self.sec_cache.add(sec, overwrite=overwrite)
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


def get_attr_by_keyword(obj: Any, kw: str, sep=".") -> Any:
    if sep not in kw:
        return getattr(obj, kw)

    idx = kw.index(sep)
    x, y = kw[:idx], kw[idx + 1 :]
    obj = getattr(obj, x)
    if len(y):
        return get_attr_by_keyword(obj, y, sep=sep)
    else:
        return obj


class SecurityChain(QuoteGrid, pydantic.BaseModel):
    """Stores derivatives and their quotes against GSIDs. Helps quickly can quickly perform business logic without re-buildling securities and qutoes."""

    underlying: Security

    def get_available_values(self, attr: str, sep=".") -> List[Any]:
        """Searches all securities in this chain, and returns list of the unique attribute values for specified attribute.

        sub-attrs can be accessed in javascript-like style
        for exercise date, for example, use attr="exercise.exercise.expiry_date"
        """
        # res = []
        # for sec in self.sec_cache:
        #     if sec not in res:
        #         res.append(get_attr_by_keyword(sec, attr))
        # return res
        return list({get_attr_by_keyword(sec, attr, sep) for sec in self.sec_cache})

    def filter(self, func: Callable[[Security], bool]):
        """Returns generator that yields all securities matching some criteria function."""
        for sec in filter(func, self.sec_cache):
            yield sec

    def subset(self, items: Optional[Dict[str, Any]] = None, sep: str = "."):
        """Iterates through all securities with attributes matching the kwargs specified."""
        if items is None:
            items = {}

        def match_func(sec: Security) -> bool:
            return all(v == get_attr_by_keyword(sec, k, sep) for k, v in items.items())

        return self.filter(match_func)

    def __len__(self):
        return len(self.sec_cache)


class FutureChain(SecurityChain, pydantic.BaseModel):
    pass


class OptionChain(SecurityChain, pydantic.BaseModel):
    pass


class FutureOptionChain(SecurityChain, pydantic.BaseModel):
    pass
