import pydantic

forbid_extra = pydantic.Extra.forbid


def placeholder():
    return None


def mmax(x, y):
    return None if x is None or y is None else max(x, y)


def mmin(x, y):
    return None if x is None or y is None else min(x, y)
