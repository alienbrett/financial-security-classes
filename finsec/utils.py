import pydantic

forbid_extra = pydantic.Extra.forbid


def placeholder():
    return None


def mmax(x, y):
    return None if x is None or y is None else max(x, y)

def mmin(x, y):
    return None if x is None or y is None else min(x, y)

def format_number(value, max_decimals):
    if isinstance(value, int):
        return f"{value}"
    else:
        format_str = f"{{:.{max_decimals}f}}"
        formatted = format_str.format(value).rstrip('0').rstrip('.')
        return formatted