from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class AssetLink:
    Role: str
    LinkedAsset: str
    Revision: str
