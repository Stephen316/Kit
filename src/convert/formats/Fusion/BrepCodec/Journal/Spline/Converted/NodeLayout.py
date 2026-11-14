from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormLinks import (
    FormLinks,
)


@MakeDataClass(frozen=True, slots=True)
class NodeLayout:
    FaceBase: int
    LoopBase: int
    SurfaceBase: int
    CoedgeBase: int
    EdgeBase: int
    VertexBase: int
    PointBase: int
    PcurveBase: int
    CurveBase: int
    BodyAttrib: int
    FaceAttribs: tuple[int, ...]
    EdgeAttribs: tuple[int, ...]
    EntityCount: int


def LabelSlots(Labels: tuple[str, ...], Start: int) -> tuple[int, ...]:
    Slots: list[int] = []
    NextSlot = Start
    for Label in Labels:
        Slots.append(NextSlot if Label else -1)
        NextSlot += 1 if Label else 0
    return tuple(Slots)


def MakeNodeLayout(Model: FormBody, Links: FormLinks, IsHistory: bool) -> NodeLayout:
    FaceCount, UseCount = len(Model.Faces), Links.UseStarts[-1]
    CoedgeBase = 4 + 3 * FaceCount
    EdgeBase = CoedgeBase + UseCount
    VertexBase = EdgeBase + len(Model.Edges)
    PointBase = VertexBase + len(Model.PointsCm)
    PcurveBase = PointBase + len(Model.PointsCm)
    CurveBase = PcurveBase + len(Links.PcurveFaces)
    AttribBase = CurveBase + Links.CurveCount
    FaceStart = AttribBase + (2 if IsHistory else 0)
    FaceAttribs = LabelSlots(
        tuple(FaceValue.Label for FaceValue in Model.Faces), FaceStart
    )
    EdgeStart = FaceStart + sum(SlotIndex >= 0 for SlotIndex in FaceAttribs)
    EdgeAttribs = LabelSlots(
        tuple(EdgeValue.Label for EdgeValue in Model.Edges), EdgeStart
    )
    return NodeLayout(
        4,
        4 + FaceCount,
        4 + 2 * FaceCount,
        CoedgeBase,
        EdgeBase,
        VertexBase,
        PointBase,
        PcurveBase,
        CurveBase,
        AttribBase if IsHistory else -1,
        FaceAttribs,
        EdgeAttribs,
        EdgeStart + sum(SlotIndex >= 0 for SlotIndex in EdgeAttribs),
    )
