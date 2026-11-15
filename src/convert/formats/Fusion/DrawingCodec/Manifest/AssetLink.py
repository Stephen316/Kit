from dataclasses import dataclass as MakeDataClass


# asset link needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class AssetLink:
    Role: str
    LinkedAsset: str
    Revision: str
