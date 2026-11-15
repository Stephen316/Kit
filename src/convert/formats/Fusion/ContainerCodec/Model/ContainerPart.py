from dataclasses import dataclass as MakeDataClass


# container part needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class ContainerPart:
    Name: str
    Payload: bytes
