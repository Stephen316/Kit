from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialIds import MaterialIds
from convert.Formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


# authored mat needs an explicit state contract so appearance references remain connected to their owning entities
@MakeDataClass(frozen=True, slots=True)
class AuthoredMat:
    Identity: MaterialIds
    Package: MaterialPackage
