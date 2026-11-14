from collections import Counter as CountItems
from math import isfinite as IsFinite, sqrt as SquareRoot

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    CylinderCarrier,
    KFaceCarrier,
    NurbsBody,
    NurbsEdge,
    NurbsFace,
    NurbsUse,
    PlaneCarrier,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsLayout import (
    EdgeRange,
    FaceLoops,
    ModelUses,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.SplineEval import (
    PointOnCurve,
    PointOnSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsCurve import (
    CheckBsCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsSurface import (
    CheckBsSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.PoleCount import PoleCount
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)

KTolerance = 1e-6


def IsNear(First: tuple[float, ...], Second: tuple[float, ...]) -> bool:
    return len(First) == len(Second) and all(
        abs(Former - Latter) <= KTolerance for Former, Latter in zip(First, Second)
    )


def DotProduct(First: tuple[float, ...], Second: tuple[float, ...]) -> float:
    return sum(Former * Latter for Former, Latter in zip(First, Second))


def VectorSize(Value: tuple[float, ...]) -> float:
    return SquareRoot(DotProduct(Value, Value))


def CheckFrame(Primary: KJournalVector, Secondary: KJournalVector) -> None:
    if not all(IsFinite(Value) for Value in (*Primary, *Secondary)):
        raise ValueError("Fusion analytic carrier requires finite vectors")
    if abs(VectorSize(Primary) - 1.0) > KTolerance:
        raise ValueError("Fusion analytic carrier requires a unit direction")
    if abs(DotProduct(Primary, Secondary)) > KTolerance:
        raise ValueError("Fusion analytic carrier axes must be perpendicular")


def CarrierGap(
    Carrier: PlaneCarrier | CylinderCarrier, Point: tuple[float, ...]
) -> float:
    Offset = tuple(
        Value - Origin for Value, Origin in zip(Point, Carrier.OriginCm, strict=True)
    )
    if isinstance(Carrier, PlaneCarrier):
        return abs(DotProduct(Offset, Carrier.Normal))
    Along = DotProduct(Offset, Carrier.AxisVector)
    Radial = tuple(
        Value - Along * AxisPart
        for Value, AxisPart in zip(Offset, Carrier.AxisVector, strict=True)
    )
    return abs(VectorSize(Radial) - VectorSize(Carrier.MajorAxisCm))


def IsCollapsed(Poles: tuple[tuple[float, ...], ...]) -> bool:
    return all(IsNear(Point, Poles[0]) for Point in Poles)


def CheckSurfForm(Surface: BsSurface) -> None:
    CheckBsSurface(Surface)
    UCount = PoleCount(Surface.UDegree, Surface.UMultiplicity)
    PoleRows = tuple(
        Surface.Poles[Start : Start + UCount]
        for Start in range(0, len(Surface.Poles), UCount)
    )
    Columns = tuple(
        tuple(PoleRow[Index] for PoleRow in PoleRows) for Index in range(UCount)
    )
    Weights = Surface.Weights or (1.0,) * len(Surface.Poles)
    WeightRows = tuple(
        Weights[Start : Start + UCount] for Start in range(0, len(Weights), UCount)
    )
    if Surface.UClosure and not all(
        IsNear(PoleRow[0], PoleRow[-1]) and IsNear(Scale[:1], Scale[-1:])
        for PoleRow, Scale in zip(PoleRows, WeightRows, strict=True)
    ):
        raise ValueError("Fusion closed U direction requires equal end columns")
    if Surface.VClosure and not (
        all(IsNear(Former, Latter) for Former, Latter in zip(PoleRows[0], PoleRows[-1]))
        and IsNear(WeightRows[0], WeightRows[-1])
    ):
        raise ValueError("Fusion closed V direction requires equal end rows")
    for FormCode, Lower, Upper in (
        (Surface.USingular, Columns[0], Columns[-1]),
        (Surface.VSingular, PoleRows[0], PoleRows[-1]),
    ):
        if FormCode in (1, 3) and not IsCollapsed(Lower):
            raise ValueError("Fusion singular low side requires one collapsed pole")
        if FormCode in (2, 3) and not IsCollapsed(Upper):
            raise ValueError("Fusion singular high side requires one collapsed pole")


def CheckCarrier(Carrier: KFaceCarrier) -> None:
    if isinstance(Carrier, BsSurface):
        CheckSurfForm(Carrier)
    elif isinstance(Carrier, PlaneCarrier):
        CheckFrame(Carrier.Normal, Carrier.ReferenceAxis)
        CheckFrame(Carrier.ReferenceAxis, Carrier.Normal)
    else:
        CheckFrame(Carrier.AxisVector, Carrier.MajorAxisCm)
        if not VectorSize(Carrier.MajorAxisCm) > KTolerance:
            raise ValueError("Fusion cylinder carrier requires a positive radius")


def UseEnds(Model: NurbsBody, UseSpec: NurbsUse) -> tuple[int, int]:
    EdgeSpec = Model.Edges[UseSpec.EdgeIndex]
    if UseSpec.Reversed:
        return EdgeSpec.EndVertex, EdgeSpec.StartVertex
    return EdgeSpec.StartVertex, EdgeSpec.EndVertex


def EdgeSamples(EdgeSpec: NurbsEdge, UseSpec: NurbsUse) -> tuple[float, ...]:
    Lower, Upper = EdgeRange(EdgeSpec)
    Knots = set(EdgeSpec.Curve.Knots)
    if UseSpec.Pcurve is not None:
        Knots |= set(UseSpec.Pcurve.Knots)
    Steps = {Lower + (Upper - Lower) * StepIndex / 16.0 for StepIndex in range(17)}
    return tuple(sorted(Steps | {Value for Value in Knots if Lower <= Value <= Upper}))


def CheckNurbsEdge(Model: NurbsBody, EdgeSpec: NurbsEdge) -> None:
    CheckBsCurve(EdgeSpec.Curve, 3)
    Lower, Upper = EdgeRange(EdgeSpec)
    if not (
        IsFinite(Lower)
        and IsFinite(Upper)
        and EdgeSpec.Curve.Knots[0] <= Lower < Upper <= EdgeSpec.Curve.Knots[-1]
    ):
        raise ValueError("Fusion NURBS edge bounds leave its curve")
    EdgeEnds = (EdgeSpec.StartVertex, EdgeSpec.EndVertex)
    if not all(
        type(Vertex) is int and 0 <= Vertex < len(Model.PointsCm) for Vertex in EdgeEnds
    ):
        raise ValueError("Fusion NURBS edge names a missing vertex")
    if not (
        IsNear(PointOnCurve(EdgeSpec.Curve, Lower), Model.PointsCm[EdgeEnds[0]])
        and IsNear(PointOnCurve(EdgeSpec.Curve, Upper), Model.PointsCm[EdgeEnds[1]])
    ):
        raise ValueError("Fusion NURBS edge curve does not meet its vertices")


def CheckSplineUse(Surface: BsSurface, EdgeSpec: NurbsEdge, UseSpec: NurbsUse) -> None:
    Pcurve = UseSpec.Pcurve
    if Pcurve is None:
        raise ValueError("Fusion NURBS spline face use requires a pcurve")
    CheckBsCurve(Pcurve, 2)
    if (Pcurve.Knots[0], Pcurve.Knots[-1]) != EdgeRange(EdgeSpec):
        raise ValueError("Fusion NURBS pcurve range must equal its edge range")
    Shifts = (UseSpec.OffsetU, UseSpec.OffsetV)
    if not all(type(Value) is float and IsFinite(Value) for Value in Shifts):
        raise ValueError("Fusion pcurve offsets must be finite doubles")
    if (Shifts[0] and not Surface.UClosure) or (Shifts[1] and not Surface.VClosure):
        raise ValueError("Fusion pcurve offset requires a closed direction")
    for Parameter in EdgeSamples(EdgeSpec, UseSpec):
        UValue, VValue = PointOnCurve(Pcurve, Parameter)
        if not IsNear(
            PointOnSurface(Surface, UValue + Shifts[0], VValue + Shifts[1]),
            PointOnCurve(EdgeSpec.Curve, Parameter),
        ):
            raise ValueError("Fusion NURBS pcurve leaves its edge on the surface")


def CheckNurbsUse(Model: NurbsBody, FaceSpec: NurbsFace, UseSpec: NurbsUse) -> None:
    EdgeSpec = Model.Edges[UseSpec.EdgeIndex]
    Carrier = FaceSpec.Surface
    if isinstance(Carrier, BsSurface):
        CheckSplineUse(Carrier, EdgeSpec, UseSpec)
        return
    if UseSpec.Pcurve is not None or UseSpec.OffsetU or UseSpec.OffsetV:
        raise ValueError("Fusion analytic face uses take no pcurve")
    for Parameter in EdgeSamples(EdgeSpec, UseSpec):
        if CarrierGap(Carrier, PointOnCurve(EdgeSpec.Curve, Parameter)) > KTolerance:
            raise ValueError("Fusion NURBS edge leaves its analytic face")


def CheckSeamPair(
    Surface: BsSurface, EdgeSpec: NurbsEdge, First: NurbsUse, Second: NurbsUse
) -> None:
    Lower = EdgeRange(EdgeSpec)[0]
    Places = tuple(
        (
            PointOnCurve(UseSpec.Pcurve, Lower)[0] + UseSpec.OffsetU,
            PointOnCurve(UseSpec.Pcurve, Lower)[1] + UseSpec.OffsetV,
        )
        for UseSpec in (First, Second)
        if UseSpec.Pcurve is not None
    )
    if len(Places) != 2:
        raise ValueError("Fusion NURBS spline face use requires a pcurve")
    Shift = (abs(Places[0][0] - Places[1][0]), abs(Places[0][1] - Places[1][1]))
    Periods = (
        Surface.UKnots[-1] - Surface.UKnots[0] if Surface.UClosure else 0.0,
        Surface.VKnots[-1] - Surface.VKnots[0] if Surface.VClosure else 0.0,
    )
    if not any(
        Periods[Course] > KTolerance
        and IsNear((Shift[Course], Shift[1 - Course]), (Periods[Course], 0.0))
        for Course in (0, 1)
    ):
        raise ValueError("Fusion seam uses must lie one period apart")


def CheckSeams(Model: NurbsBody, FaceSpec: NurbsFace) -> None:
    Surface = FaceSpec.Surface
    if not isinstance(Surface, BsSurface):
        return
    FaceUses = tuple(
        UseSpec for LoopUses in FaceLoops(FaceSpec) for UseSpec in LoopUses
    )
    for EdgeIndex in sorted({UseSpec.EdgeIndex for UseSpec in FaceUses}):
        SeamUses = tuple(
            UseSpec for UseSpec in FaceUses if UseSpec.EdgeIndex == EdgeIndex
        )
        if len(SeamUses) == 2:
            CheckSeamPair(Surface, Model.Edges[EdgeIndex], SeamUses[0], SeamUses[1])


def CheckNurbsLoop(Model: NurbsBody, FaceSpec: NurbsFace) -> None:
    CheckCarrier(FaceSpec.Surface)
    for LoopUses in FaceLoops(FaceSpec):
        if not LoopUses:
            raise ValueError("Fusion NURBS face loops must not be empty")
        for Index, UseSpec in enumerate(LoopUses):
            Following = LoopUses[(Index + 1) % len(LoopUses)]
            if UseEnds(Model, UseSpec)[1] != UseEnds(Model, Following)[0]:
                raise ValueError("Fusion NURBS loop uses do not connect")
            CheckNurbsUse(Model, FaceSpec, UseSpec)
    CheckSeams(Model, FaceSpec)


def CheckNurbsBody(Model: NurbsBody) -> None:
    if not Model.Faces or not Model.Edges or not 1 <= len(Model.PointsCm) <= 4096:
        raise ValueError("Fusion NURBS body requires faces, edges and vertices")
    Vertices = {
        Vertex
        for EdgeSpec in Model.Edges
        for Vertex in (EdgeSpec.StartVertex, EdgeSpec.EndVertex)
    }
    if Vertices != set(range(len(Model.PointsCm))):
        raise ValueError("Fusion NURBS vertices must all bound some edge")
    UseSpecs = ModelUses(Model)
    Counts = CountItems(UseSpec.EdgeIndex for UseSpec in UseSpecs)
    if set(Counts) != set(range(len(Model.Edges))) or not set(Counts.values()) <= {
        1,
        2,
    }:
        raise ValueError("Fusion NURBS edges need one or two uses each")
    for EdgeIndex, Count in Counts.items():
        Senses = {
            UseSpec.Reversed for UseSpec in UseSpecs if UseSpec.EdgeIndex == EdgeIndex
        }
        if Count == 2 and Senses != {False, True}:
            raise ValueError("Fusion NURBS shared edge needs opposite coedge senses")
    for EdgeSpec in Model.Edges:
        CheckNurbsEdge(Model, EdgeSpec)
    for FaceSpec in Model.Faces:
        CheckNurbsLoop(Model, FaceSpec)
