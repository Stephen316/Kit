from dataclasses import dataclass


@dataclass(frozen=True)
class ProtoField:
    Number: int
    Value: int | bytes
