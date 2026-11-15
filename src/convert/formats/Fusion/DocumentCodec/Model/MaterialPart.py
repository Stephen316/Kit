from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


# material part needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class MaterialPart:
    Name: str
    Package: MaterialPackage
