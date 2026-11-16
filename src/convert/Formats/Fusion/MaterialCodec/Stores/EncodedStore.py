from dataclasses import dataclass as MakeDataClass


# encoded store needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class EncodedStore:
    Payload: bytes
    Roots: tuple[int, ...]
