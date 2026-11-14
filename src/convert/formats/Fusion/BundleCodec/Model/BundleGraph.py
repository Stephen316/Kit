from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BundleCodec.Model.BundleObject import BundleObject


@MakeDataClass(frozen=True, slots=True)
class BundleGraph:
    CreatedAt: str
    ServiceName: str
    RootIds: tuple[int, ...]
    Objects: tuple[BundleObject, ...]
