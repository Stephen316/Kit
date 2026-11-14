from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.LinkAuthor.Model.LinkTarget import LinkTarget
from convert.formats.Fusion.LinkAuthor.Model.PlacedPart import PlacedPart
from convert.formats.Fusion.LinkAuthor.Model.RigidJoint import RigidJoint


@MakeDataClass(frozen=True, slots=True)
class AssemblySpec:
    Base: DocumentSpec
    Targets: tuple[LinkTarget, ...]
    Placements: tuple[PlacedPart, ...]
    Joint: RigidJoint | None = None
    SourcePath: str = "KitAssembly.f3d"
