from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Revolves.OriginAxis import KAxisGuid
from convert.Formats.Fusion.Revolves.RevolveEdge import ResolveRevEdge
from convert.Formats.Fusion.Revolves.RevolvePick import RevolvePick
from convert.Formats.Fusion.SelectionProxy import ReadSelectDesc
from convert.Formats.Fusion.SelectionRef import (
    KSelectLeaf,
    ReadEntityLeaf,
    ReadDescLeaf,
)
from convert.Formats.Fusion.Sketches.SketchPick import FindSketchCurve, ReadSketchPick
from convert.Formats.Fusion.Topology.PickDescriptor import KTopoSelect
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import SelectPathElem
from interchange.geometry.Models.Sketch import Sketch


# axes dispatch by descriptor class before resolving construction or topology sources
def ResolveRevAxis(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SelectId: int,
    FeatureId: int,
    FeatureOrder: int,
    SketchLinks: dict[int, tuple[Sketch, FeatureStep]],
    FeatureLinks: dict[int, FeatureStep],
) -> RevolvePick:
    Descriptor = ReadSelectDesc(BulkData, Owners, SelectId, FeatureId)
    SpanValue = Owners.get(Descriptor)
    if SpanValue is not None and SpanValue.ClassGuid == KTopoSelect:
        return ResolveRevEdge(
            BulkData, Owners, Descriptor, FeatureId, FeatureOrder, FeatureLinks
        )
    Terminal = ReadDescLeaf(BulkData, Owners, Descriptor, FeatureId)
    LeafValue = Owners.get(Terminal)
    if LeafValue is not None and LeafValue.ClassGuid == KSelectLeaf:
        EntityId = ReadEntityLeaf(BulkData, Owners, Terminal)
        Source = Owners.get(EntityId)
        if Source is None or Source.ClassGuid != KAxisGuid:
            raise ValueError("Unsupported Fusion Revolve construction axis")
        return RevolvePick(EntityId, Descriptor, Terminal)
    SketchId, TagValue = ReadSketchPick(BulkData, Owners, Terminal)
    SourceLink = SketchLinks.get(SketchId)
    if SourceLink is None or SourceLink[1].order >= FeatureOrder:
        raise ValueError("Fusion Revolve axis sketch is outside prior history")
    SketchValue, SketchStep = SourceLink
    Entity = FindSketchCurve(SketchValue, TagValue)
    Geometry = Entity.geometry
    if (
        not isinstance(Geometry, LineGeometry)
        or Geometry.start == Geometry.end
        or Entity.provenance is None
    ):
        raise ValueError("Fusion Revolve axis selection requires a directed line")
    return RevolvePick(
        int(Entity.provenance.native_id),
        Descriptor,
        Terminal,
        (
            SelectPathElem("sketch", SketchValue.id),
            SelectPathElem("sketch_entity", Entity.id),
        ),
        SketchStep.id,
    )
