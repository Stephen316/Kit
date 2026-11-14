from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class RootAsset:
    Name: str
    Word: int
    Flag: int
