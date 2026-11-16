from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.Formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo


# package folder needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class PackageFolder:
    Core: PackageCore
    Folders: tuple["PackageFolder", ...] = ()
    Links: tuple[ResourceInfo, ...] = ()
    Contents: tuple[bytes, ...] = ()
