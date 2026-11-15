from dataclasses import dataclass as MakeDataClass


# root asset needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class RootAsset:
    Name: str
    Word: int
    Flag: int
