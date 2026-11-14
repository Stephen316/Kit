from dataclasses import dataclass as MakeDataClass
from typing import Literal


@MakeDataClass(frozen=True, slots=True)
class KeywordToken:
    Value: Literal["I", "forward", "reversed", "single", "forward_v"]
