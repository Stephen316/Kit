from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo


@MakeDataClass(frozen=True, slots=True)
class PackageFolder:
    Core: PackageCore
    Folders: tuple["PackageFolder", ...] = ()
    Links: tuple[ResourceInfo, ...] = ()
    Contents: tuple[bytes, ...] = ()
