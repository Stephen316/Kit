from dataclasses import dataclass as MakeDataClass
from typing import Literal


@MakeDataClass(frozen=True, slots=True)
class ConfigPart:
    Name: str
    KindValue: Literal["table", "rule"]
