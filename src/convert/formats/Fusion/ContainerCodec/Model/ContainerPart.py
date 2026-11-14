from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ContainerPart:
    Name: str
    Payload: bytes
