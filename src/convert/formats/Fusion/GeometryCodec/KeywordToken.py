from dataclasses import dataclass as MakeDataClass
from typing import Literal


# keyword token needs an explicit state contract so geometric values retain their native record boundaries
@MakeDataClass(frozen=True, slots=True)
class KeywordToken:
    Value: Literal["I", "forward", "reversed", "single", "forward_v"]
