import enum


def format_value(v):
    if isinstance(v, enum.Enum):
        return v.name
    elif isinstance(v, list) and len(v) < 1:
        return None
    else:
        return v


def pretty_print_security(sec):
    res = "Security("
    # stuff = {k:(v.name if isinstance(v, enum.Enum) else v) for k, v in sec.model_dump().items() if v is not None}
    for k, v in sec.model_dump().items():
        v = format_value(v)
        if v is not None:
            res += f"{k}=[{v}], "
    res = res[:-2] + ")"
    return res
