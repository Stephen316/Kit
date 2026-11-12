from interchange.geometry.models.Transform import Transform
from math import hypot as Hypot, isfinite as IsFinite

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.OriginAxis import KComponentGuid
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs
from convert.formats.Fusion.Sketches.SketchFrame import ReadFrame
from convert.formats.Fusion.Sketches.SketchPick import FindSketchCurve, ReadSketchPick
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from convert.formats.Fusion.Topology.PickSupport import ReadPickSupport
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.topology.BrepMath import IsFiniteSpace
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import KOriginZero
from interchange.geometry.models.VectorSpace import SpaceVector

# typed sketch roots own the native curve tag namespace
KSketchGuid = "44A64366-4BD3-4B24-881A-F94C206E8F2D"

# only native line primitives supply directed endpoints for an angular axis
KLineGuid = "DCA267ED-D615-4934-B64F-AD805E8003E2"

# sketch placements use one class for both identity and rigid transforms
KFrameGuid = "F47A46FB-DA27-4AFA-8A72-1B38FA596E23"


# selected line endpoints remain ordered when projected to their shared component
def ReadSketchAxis(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    PickValue: Selection,
    Sketches: dict[str, Sketch],
    Frames: dict[str, SupportPlane],
    ComponentId: int,
    AxisId: int,
    Descriptor: int,
    Terminal: int,
    SupportId: int,
) -> tuple[SpaceVector, SpaceVector]:
    if tuple(Element.entity_kind for Element in PickValue.path) != (
        "sketch",
        "sketch_entity",
    ):
        raise ValueError(
            "Fusion Revolve sketch axis requires a sketch and line selection path"
        )
    SketchRoot, CurveTag = ReadSketchPick(BulkData, Owners, Terminal)
    SketchValue = Sketches.get(PickValue.path[0].entity_id)
    if (
        SketchValue is None
        or SketchValue.provenance is None
        or SketchValue.provenance.native_id != str(SketchRoot)
    ):
        raise ValueError("Fusion Revolve sketch axis native root disagrees")
    RootCursor = SelectCursor(BulkData, Owners, SketchRoot, KSketchGuid)
    RootCursor.Offset = len(RootCursor.DataValue) - 15
    SketchOwner = ReadNativeRef(RootCursor)
    _ = SelectCursor(BulkData, Owners, SketchOwner, KSketchFeature)
    ReadPickSupport(BulkData, Owners, SupportId, Descriptor, SketchOwner)
    LineValue = FindSketchCurve(SketchValue, CurveTag)
    Geometry = LineValue.geometry
    if (
        LineValue.id != PickValue.path[1].entity_id
        or LineValue.provenance is None
        or LineValue.provenance.native_id != str(AxisId)
        or not isinstance(Geometry, LineGeometry)
    ):
        raise ValueError("Fusion Revolve sketch axis native line disagrees")
    LineCursor = SelectCursor(BulkData, Owners, AxisId, KLineGuid)
    Props = ReadGeomAttrs(LineCursor)
    LineCursor.Offset = len(LineCursor.DataValue) - 11
    if (
        Props.get("crv_primary_id") != CurveTag
        or ReadNativeRef(LineCursor) != SketchRoot
    ):
        raise ValueError("Fusion Revolve sketch axis line owner or tag disagrees")
    FrameValue = Frames.get(SketchValue.support_plane_id)
    if (
        FrameValue is None
        or FrameValue.id != f"fusion-sketch-frame-{SketchRoot}"
        or FrameValue.provenance is None
    ):
        raise ValueError("Missing Fusion Revolve sketch axis placement")
    FrameId = int(FrameValue.provenance.native_id)
    Frame, FrameComponent = ReadFrame(
        SelectCursor(BulkData, Owners, FrameId, KFrameGuid).DataValue
    )
    if FrameComponent != ComponentId or FrameValue.transform != Frame:
        raise ValueError("Fusion Revolve sketch axis component or frame disagrees")
    _ = SelectCursor(BulkData, Owners, FrameComponent, KComponentGuid)
    return MakeSketchAxis(Geometry, Frame)


# world axis construction rejects coincident or nonfinite endpoints
def MakeSketchAxis(
    Geometry: LineGeometry, Frame: Transform
) -> tuple[SpaceVector, SpaceVector]:
    Start, Finish = Geometry.start, Geometry.end
    OriginPoint = OffsetVector(
        OffsetVector(Frame.origin, Frame.x_axis, Start.x), Frame.y_axis, Start.y
    )
    Delta = OffsetVector(
        OffsetVector(KOriginZero, Frame.x_axis, Finish.x - Start.x),
        Frame.y_axis,
        Finish.y - Start.y,
    )
    Length = Hypot(Delta.x, Delta.y, Delta.z)
    if (
        not IsFiniteSpace(OriginPoint)
        or not IsFiniteSpace(OffsetVector(OriginPoint, Delta, 1.0))
        or not IsFinite(Length)
        or Length <= 1e-8
    ):
        raise ValueError("Invalid Fusion Revolve sketch axis endpoints")
    return OriginPoint, SpaceVector(
        Delta.x / Length, Delta.y / Length, Delta.z / Length
    )
