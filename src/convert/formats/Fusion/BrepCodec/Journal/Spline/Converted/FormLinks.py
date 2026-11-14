from dataclasses import dataclass as MakeDataClass
from itertools import accumulate as Accumulate

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormUse,
)


@MakeDataClass(frozen=True, slots=True)
class FormLinks:
    UseStarts: tuple[int, ...]
    EdgeOwners: tuple[int, ...]
    VertexOwners: tuple[tuple[int, int], ...]
    Partners: tuple[int, ...]
    CurveSlots: tuple[int, ...]
    CurveCount: int
    PcurveSlots: tuple[int, ...]
    PcurveFaces: tuple[int, ...]


def CreationUses(Model: FormBody, Starts: tuple[int, ...]) -> list[tuple[int, FormUse]]:
    Created = sorted(
        range(len(Model.Faces)),
        key=lambda FaceIndex: Model.Faces[FaceIndex].Surface.Region,
    )
    return [
        (Starts[FaceIndex] + Offset, UseValue)
        for FaceIndex in Created
        for Offset, UseValue in enumerate(Model.Faces[FaceIndex].Uses)
    ]


def UseOwners(
    Model: FormBody, Starts: tuple[int, ...]
) -> tuple[tuple[int, ...], tuple[tuple[int, int], ...]]:
    EdgeOwners: dict[int, int] = {}
    VertexOwners: dict[int, tuple[int, int]] = {}
    for Ordinal, UseValue in CreationUses(Model, Starts):
        _ = EdgeOwners.setdefault(UseValue.EdgeIndex, Ordinal)
        EdgeValue = Model.Edges[UseValue.EdgeIndex]
        for EndIndex, Vertex in enumerate((EdgeValue.StartVertex, EdgeValue.EndVertex)):
            _ = VertexOwners.setdefault(Vertex, (UseValue.EdgeIndex, EndIndex))
    for EdgeIndex, EdgeValue in enumerate(Model.Edges):
        if (
            EdgeValue.Bounds is not None
            and EdgeValue.Bounds[0] > EdgeValue.Curve.Knots[0]
        ):
            VertexOwners[EdgeValue.StartVertex] = (EdgeIndex, 0)
    return (
        tuple(EdgeOwners[Index] for Index in range(len(Model.Edges))),
        tuple(VertexOwners[Index] for Index in range(len(Model.PointsCm))),
    )


def UsePartners(Model: FormBody) -> tuple[int, ...]:
    FlatUses = tuple(
        UseValue for FaceValue in Model.Faces for UseValue in FaceValue.Uses
    )
    Users: dict[int, list[int]] = {}
    for Ordinal, UseValue in enumerate(FlatUses):
        Users.setdefault(UseValue.EdgeIndex, []).append(Ordinal)
    return tuple(
        next(
            (Other for Other in Users[UseValue.EdgeIndex] if Other != Ordinal),
            -1,
        )
        for Ordinal, UseValue in enumerate(FlatUses)
    )


def MakeFormLinks(Model: FormBody) -> FormLinks:
    Starts = (0, *Accumulate(len(FaceValue.Uses) for FaceValue in Model.Faces))
    EdgeOwners, VertexOwners = UseOwners(Model, Starts)
    Shared: dict[object, int] = {}
    CurveSlots = tuple(
        Shared.setdefault((EdgeValue.Curve, EdgeValue.Jumps), len(Shared))
        for EdgeValue in Model.Edges
    )
    Traces: dict[tuple[int, bool, object, float], int] = {}
    PcurveSlots = tuple(
        Traces.setdefault(
            (FaceIndex, UseValue.Reversed, UseValue.Pcurve, UseValue.Fit), len(Traces)
        )
        for FaceIndex, FaceValue in enumerate(Model.Faces)
        for UseValue in FaceValue.Uses
    )
    return FormLinks(
        Starts,
        EdgeOwners,
        VertexOwners,
        UsePartners(Model),
        CurveSlots,
        len(Shared),
        PcurveSlots,
        tuple(TraceKey[0] for TraceKey in Traces),
    )
