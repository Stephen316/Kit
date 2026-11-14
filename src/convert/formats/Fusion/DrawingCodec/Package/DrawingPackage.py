from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Package.PackageEntry import PackageEntry


@MakeDataClass(frozen=True, slots=True)
class DrawingPackage:
    Entries: tuple[PackageEntry, ...]
