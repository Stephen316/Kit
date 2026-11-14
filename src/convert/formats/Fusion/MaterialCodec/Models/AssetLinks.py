from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class AssetLinks:
    Enabled: bool
    Targets: tuple[str, ...]
