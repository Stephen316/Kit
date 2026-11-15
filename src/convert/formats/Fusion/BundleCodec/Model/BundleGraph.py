from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BundleCodec.Model.BundleObject import BundleObject


# bundle graph needs an explicit state contract so linked archive members retain their document relationships
@MakeDataClass(frozen=True, slots=True)
class BundleGraph:
    CreatedAt: str
    ServiceName: str
    RootIds: tuple[int, ...]
    Objects: tuple[BundleObject, ...]
