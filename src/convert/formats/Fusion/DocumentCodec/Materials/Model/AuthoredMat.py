from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialIds import MaterialIds
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


@MakeDataClass(frozen=True, slots=True)
class AuthoredMat:
    Identity: MaterialIds
    Package: MaterialPackage
