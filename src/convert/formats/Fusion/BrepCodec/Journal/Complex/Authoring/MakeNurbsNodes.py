from math import dist as Distance

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    ExactCurve,
    ExactSurface,
    ParamCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NegateCurve import (
    NegateCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    CylinderCarrier,
    KFaceCarrier,
    NurbsBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsLayout import (
    EdgeRange,
    NurbsLayout,
    ModelUses,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import (
    IntcurveNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode

KBlankPrefix = EntityPrefix(-1, -1)


def MakeCarrier(Carrier: KFaceCarrier) -> SplineNode | PlaneNode | ConeNode:
    if isinstance(Carrier, BsSurface):
        return SplineNode(
            KBlankPrefix, False, ExactSurface(Carrier), None, None, None, None
        )
    if isinstance(Carrier, CylinderCarrier):
        return ConeNode(
            KBlankPrefix,
            Carrier.OriginCm,
            Carrier.AxisVector,
            Carrier.MajorAxisCm,
            1.0,
            None,
            None,
            0.0,
            1.0,
            Distance(Carrier.MajorAxisCm, (0.0, 0.0, 0.0)),
            False,
            None,
            None,
            None,
            None,
        )
    return PlaneNode(
        KBlankPrefix,
        Carrier.OriginCm,
        Carrier.Normal,
        Carrier.ReferenceAxis,
        False,
        None,
        None,
        None,
        None,
    )


def MakeNurbsFaces(
    Model: NurbsBody, Layout: NurbsLayout
) -> tuple[FaceNode | LoopNode | SplineNode | PlaneNode | ConeNode, ...]:
    FaceCount = len(Model.Faces)
    Faces = tuple(
        FaceNode(
            KBlankPrefix,
            Layout.FaceBase + Index + 1 if Index + 1 < FaceCount else -1,
            Layout.LoopBase + Layout.LoopStarts[Index],
            3,
            Layout.SurfaceBase + Index,
            False,
            False,
            None,
        )
        for Index in range(FaceCount)
    )
    Loops = tuple(
        LoopNode(
            KBlankPrefix,
            (
                Layout.LoopBase + LoopIndex + 1
                if LoopIndex + 1 < Layout.LoopStarts[FaceIndex + 1]
                else -1
            ),
            Layout.CoedgeBase + Layout.UseStarts[LoopIndex],
            Layout.FaceBase + FaceIndex,
        )
        for LoopIndex, FaceIndex in enumerate(Layout.LoopFaces)
    )
    Surfaces = tuple(MakeCarrier(FaceSpec.Surface) for FaceSpec in Model.Faces)
    return (*Faces, *Loops, *Surfaces)


def MakeNurbsUses(Model: NurbsBody, Layout: NurbsLayout) -> tuple[CoedgeNode, ...]:
    UseList = ModelUses(Model)
    Results: list[CoedgeNode] = []
    for Global, UseSpec in enumerate(UseList):
        LoopIndex = Layout.UseLoops[Global]
        Start = Layout.UseStarts[LoopIndex]
        Length = Layout.UseStarts[LoopIndex + 1] - Start
        Offset = Global - Start
        Partner = next(
            (
                Layout.CoedgeBase + Other
                for Other, Candidate in enumerate(UseList)
                if Other != Global and Candidate.EdgeIndex == UseSpec.EdgeIndex
            ),
            -1,
        )
        PcurveSlot = Layout.PcurveSlots[Global]
        Results.append(
            CoedgeNode(
                KBlankPrefix,
                Layout.CoedgeBase + Start + (Offset + 1) % Length,
                Layout.CoedgeBase + Start + (Offset - 1) % Length,
                Partner,
                Layout.EdgeBase + UseSpec.EdgeIndex,
                UseSpec.Reversed,
                Layout.LoopBase + LoopIndex,
                Layout.PcurveBase + PcurveSlot if PcurveSlot >= 0 else -1,
            )
        )
    return tuple(Results)


def MakeNurbsEdges(
    Model: NurbsBody, Layout: NurbsLayout, Coedges: tuple[CoedgeNode, ...]
) -> tuple[EdgeNode | VertexNode | PointNode, ...]:
    Edges = tuple(
        EdgeNode(
            KBlankPrefix,
            Layout.VertexBase + EdgeSpec.StartVertex,
            EdgeRange(EdgeSpec)[0],
            Layout.VertexBase + EdgeSpec.EndVertex,
            EdgeRange(EdgeSpec)[1],
            Layout.CoedgeBase
            + next(
                Ordinal
                for Ordinal, Coedge in enumerate(Coedges)
                if Coedge.EdgeRef == Layout.EdgeBase + Index
            ),
            Layout.CurveBase + Index,
            False,
            "unknown",
        )
        for Index, EdgeSpec in enumerate(Model.Edges)
    )
    Owners = tuple(
        next(
            (Index, 0 if EdgeSpec.StartVertex == Vertex else 1)
            for Index, EdgeSpec in enumerate(Model.Edges)
            if Vertex in (EdgeSpec.StartVertex, EdgeSpec.EndVertex)
        )
        for Vertex in range(len(Model.PointsCm))
    )
    Vertices = tuple(
        VertexNode(
            KBlankPrefix, Layout.EdgeBase + Owner, EdgeEnd, Layout.PointBase + Vertex
        )
        for Vertex, (Owner, EdgeEnd) in enumerate(Owners)
    )
    Points = tuple(PointNode(KBlankPrefix, Point) for Point in Model.PointsCm)
    return (*Edges, *Vertices, *Points)


def MakeNurbsCurves(
    Model: NurbsBody, Layout: NurbsLayout
) -> tuple[PcurveNode | IntcurveNode, ...]:
    UseList = ModelUses(Model)
    Pcurves = tuple(
        PcurveNode(
            KBlankPrefix,
            False,
            ParamCurve(
                NegateCurve(UseSpec.Pcurve) if UseSpec.Reversed else UseSpec.Pcurve,
                Layout.TableSlots[Layout.LoopFaces[Layout.UseLoops[Global]]],
            ),
            UseSpec.OffsetU,
            UseSpec.OffsetV,
        )
        for Global, UseSpec in enumerate(UseList)
        if UseSpec.Pcurve is not None
    )
    Curves = tuple(
        IntcurveNode(
            KBlankPrefix,
            False,
            ExactCurve(EdgeSpec.Curve),
            EdgeSpec.Curve.Knots[0],
            EdgeSpec.Curve.Knots[-1],
        )
        for EdgeSpec in Model.Edges
    )
    return (*Pcurves, *Curves)
