from dataclasses import dataclass as MakeDataClass


# asset links needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class AssetLinks:
    Enabled: bool
    Targets: tuple[str, ...]
