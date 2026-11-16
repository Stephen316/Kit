from dataclasses import dataclass as MakeDataClass
from typing import Literal


# config part needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class ConfigPart:
    Name: str
    KindValue: Literal["table", "rule"]
