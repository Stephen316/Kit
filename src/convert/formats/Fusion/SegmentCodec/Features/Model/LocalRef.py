from dataclasses import dataclass as MakeDataClass


# local reference needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class LocalRef:
    ObjectId: int
