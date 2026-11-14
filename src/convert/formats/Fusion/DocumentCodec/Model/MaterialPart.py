from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


@MakeDataClass(frozen=True, slots=True)
class MaterialPart:
    Name: str
    Package: MaterialPackage
