from dataclasses import dataclass


# proto field needs an explicit state contract so vertex and index streams retain their intended connectivity
@dataclass(frozen=True)
class ProtoField:
    Number: int
    Value: int | bytes
