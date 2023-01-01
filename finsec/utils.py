import pydantic


class MissingTimezone(Exception):
    pass


def placeholder():
    return None


forbid_extra = pydantic.Extra.forbid
