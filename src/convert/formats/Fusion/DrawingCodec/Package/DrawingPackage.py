from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Package.PackageEntry import PackageEntry


# drawing package needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class DrawingPackage:
    Entries: tuple[PackageEntry, ...]
