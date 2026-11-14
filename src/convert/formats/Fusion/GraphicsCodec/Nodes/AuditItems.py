from convert.formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedEdge import EnhancedEdge
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedFace import EnhancedFace


def AuditItems(
    EdgeNodes: tuple[LodValue, ...], FaceNodes: tuple[LodValue, ...]
) -> None:
    EdgeTotal = sum(isinstance(Entry.Geometry, EnhancedEdge) for Entry in EdgeNodes)
    if (
        any(isinstance(Entry.Geometry, EnhancedFace) for Entry in EdgeNodes)
        or any(isinstance(Entry.Geometry, EnhancedEdge) for Entry in FaceNodes)
        or any(
            Number >= EdgeTotal
            for Entry in FaceNodes
            if isinstance(Entry.Geometry, EnhancedFace)
            for Number in Entry.Geometry.EdgeIds
        )
    ):
        raise ValueError("Unsupported graphics enhanced display item references")
