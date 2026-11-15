from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Sketches.FaceSupport.FaceRecipes import KEdgeNames
from interchange.geometry.models.Selection import Selection


# the typed recipe stays available for joining exact operands after design support is published
@MakeDataClass(frozen=True, slots=True)
class FaceRecipePick:
    SelectionValue: Selection
    BodyName: str
    FaceName: str
    Boundary: frozenset[KEdgeNames]
    ContextEdges: tuple[tuple[int, int, KEdgeNames], ...]
