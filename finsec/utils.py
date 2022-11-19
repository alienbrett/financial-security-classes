import pydantic


class MissingTimezone(Exception):
    pass

placeholder = lambda: None
forbid_extra = pydantic.Extra.forbid
