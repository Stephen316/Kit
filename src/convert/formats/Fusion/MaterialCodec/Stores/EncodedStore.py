from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class EncodedStore:
    Payload: bytes
    Roots: tuple[int, ...]
