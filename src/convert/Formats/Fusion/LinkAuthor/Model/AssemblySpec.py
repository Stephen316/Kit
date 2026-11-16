from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.LinkAuthor.Model.LinkTarget import LinkTarget
from convert.Formats.Fusion.LinkAuthor.Model.PlacedPart import PlacedPart
from convert.Formats.Fusion.LinkAuthor.Model.RigidJoint import RigidJoint


# assembly specification needs an explicit state contract so cross document references retain their intended ownership
@MakeDataClass(frozen=True, slots=True)
class AssemblySpec:
    Base: DocumentSpec
    Targets: tuple[LinkTarget, ...]
    Placements: tuple[PlacedPart, ...]
    Joint: RigidJoint | None = None
    SourcePath: str = "KitAssembly.f3d"
