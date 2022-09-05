# from dataclasses import dataclass, field
import dataclasses_json
import datetime
import typing


def optional_datetime_encoder(dt : typing.Optional[datetime.datetime]) -> typing.Optional[str]:
    if dt is None:
        return None
    else:
        return datetime.datetime.isoformat(dt)


def optional_datetime_decoder(x : typing.Optional[str] ) -> typing.Optional[datetime.datetime]:
    if x is None:
        return None
    else:
        return datetime.datetime.fromisoformat(x)



date_field_config = dataclasses_json.config(
    encoder= datetime.date.isoformat,
    decoder= datetime.date.fromisoformat,
)

datetime_field_config = dataclasses_json.config(
    encoder= datetime.datetime.isoformat,
    decoder= datetime.datetime.fromisoformat,
)


maybe_datetime_field_config = dataclasses_json.config(
    encoder= optional_datetime_encoder,
    decoder= optional_datetime_decoder,
)