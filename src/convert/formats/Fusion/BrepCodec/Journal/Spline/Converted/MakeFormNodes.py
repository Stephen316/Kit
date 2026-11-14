from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NegateCurve import (
    NegateCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    ExpParCur,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormCurve import (
    FormCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormLinks import (
    FormLinks,
    MakeFormLinks,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormMarks import (
    FormMarks,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.NodeLayout import (
    MakeNodeLayout,
    NodeLayout,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

KBlankPrefix = EntityPrefix(-1, -1)
KSurfaceSlot = SubtypeRef("surface", 0)
KOpenBounds = (None, None, None, None)


@MakeDataClass(frozen=True, slots=True)
class FormDraft:
    Entities: tuple[KJournalEntity, ...]
    Carriers: tuple[int, ...]
    Surfaces: tuple[TsplineSurf, ...]


def EdgeBounds(Value: FormEdge) -> tuple[float, float]:
    if Value.Bounds is not None:
        return Value.Bounds
    return (Value.Curve.Knots[0], Value.Curve.Knots[-1])


def MakeShellNodes(Layout: NodeLayout, IsHistory: bool) -> tuple[KJournalEntity, ...]:
    return (
        AsmRoot(-1, -1, "232.5.0.65535"),
        BodyNode(EntityPrefix(Layout.BodyAttrib, 0 if IsHistory else -1), 2, -1),
        LumpNode(KBlankPrefix, -1, 3, 1),
        ShellNode(KBlankPrefix, -1, Layout.FaceBase, 2),
    )


def MakeFaceNodes(
    Model: FormBody, Links: FormLinks, Layout: NodeLayout
) -> tuple[KJournalEntity, ...]:
    Count = len(Model.Faces)
    Faces = tuple(
        FaceNode(
            EntityPrefix(Layout.FaceAttribs[Index], -1),
            Layout.FaceBase + Index + 1 if Index + 1 < Count else -1,
            Layout.LoopBase + Index,
            3,
            Layout.SurfaceBase + Index,
            False,
            FaceValue.DoubleSided,
            FaceValue.Contained,
        )
        for Index, FaceValue in enumerate(Model.Faces)
    )
    Loops = tuple(
        LoopNode(
            KBlankPrefix,
            -1,
            Layout.CoedgeBase + Links.UseStarts[Index],
            Layout.FaceBase + Index,
        )
        for Index in range(Count)
    )
    Surfaces = tuple(
        SplineNode(KBlankPrefix, False, KSurfaceSlot, None, None, None, None)
        for _ in range(Count)
    )
    return (*Faces, *Loops, *Surfaces)


def MakeUseNodes(
    Model: FormBody, Links: FormLinks, Layout: NodeLayout
) -> tuple[CoedgeNode, ...]:
    Results: list[CoedgeNode] = []
    for FaceIndex, FaceValue in enumerate(Model.Faces):
        First = Links.UseStarts[FaceIndex]
        Length = len(FaceValue.Uses)
        for Offset, UseValue in enumerate(FaceValue.Uses):
            Partner = Links.Partners[First + Offset]
            Results.append(
                CoedgeNode(
                    KBlankPrefix,
                    Layout.CoedgeBase + First + (Offset + 1) % Length,
                    Layout.CoedgeBase + First + (Offset - 1) % Length,
                    Layout.CoedgeBase + Partner if Partner >= 0 else -1,
                    Layout.EdgeBase + UseValue.EdgeIndex,
                    UseValue.Reversed,
                    Layout.LoopBase + FaceIndex,
                    Layout.PcurveBase + Links.PcurveSlots[First + Offset],
                )
            )
    return tuple(Results)


def MakeEdgeNodes(
    Model: FormBody, Links: FormLinks, Layout: NodeLayout
) -> tuple[KJournalEntity, ...]:
    Edges = tuple(
        EdgeNode(
            EntityPrefix(Layout.EdgeAttribs[Index], -1),
            Layout.VertexBase + EdgeValue.StartVertex,
            EdgeBounds(EdgeValue)[0],
            Layout.VertexBase + EdgeValue.EndVertex,
            EdgeBounds(EdgeValue)[1],
            Layout.CoedgeBase + Links.EdgeOwners[Index],
            Layout.CurveBase + Links.CurveSlots[Index],
            False,
            EdgeValue.Convexity,
        )
        for Index, EdgeValue in enumerate(Model.Edges)
    )
    Vertices = tuple(
        VertexNode(
            KBlankPrefix,
            Layout.EdgeBase + EdgeIndex,
            EndIndex,
            Layout.PointBase + Index,
        )
        for Index, (EdgeIndex, EndIndex) in enumerate(Links.VertexOwners)
    )
    Points = tuple(
        PointNode(KBlankPrefix, (float(Point[0]), float(Point[1]), float(Point[2])))
        for Point in Model.PointsCm
    )
    return (*Edges, *Vertices, *Points)


def MakeCurveNodes(Model: FormBody, Links: FormLinks) -> tuple[KJournalEntity, ...]:
    FlatUses = tuple(
        UseValue for FaceValue in Model.Faces for UseValue in FaceValue.Uses
    )
    Traces: dict[int, FormUse] = {}
    for Ordinal, PcurveSlot in enumerate(Links.PcurveSlots):
        _ = Traces.setdefault(PcurveSlot, FlatUses[Ordinal])
    Pcurves = tuple(
        PcurveNode(
            KBlankPrefix,
            False,
            SubtypeNode(
                "exp_par_cur",
                ExpParCur(
                    (
                        NegateCurve(UseValue.Pcurve)
                        if UseValue.Reversed
                        else UseValue.Pcurve
                    ),
                    float(UseValue.Fit),
                    ChoiceValue("spline", (False, KSurfaceSlot, KOpenBounds)),
                ),
            ),
            0.0,
            0.0,
        )
        for UseValue in (Traces[PcurveSlot] for PcurveSlot in range(len(Traces)))
    )
    Firsts: dict[int, FormEdge] = {}
    for Index, CurveSlot in enumerate(Links.CurveSlots):
        _ = Firsts.setdefault(CurveSlot, Model.Edges[Index])
    Curves = tuple(
        IntcurveNode(
            KBlankPrefix,
            False,
            FormCurve(Firsts[CurveSlot].Curve, Firsts[CurveSlot].Jumps),
            None,
            None,
        )
        for CurveSlot in range(Links.CurveCount)
    )
    return (*Pcurves, *Curves)


def MakeTagNodes(
    Model: FormBody, Layout: NodeLayout, Marks: FormMarks
) -> tuple[KJournalEntity, ...]:
    Operation = (Marks.FeatureId + 1,)
    Results: list[KJournalEntity] = []
    if Layout.BodyAttrib >= 0:
        BodyTag = FeatureTag(str(Marks.FeatureId), (), 1, 0)
        Results.append(
            TimeAttrib(
                AttribLinks(Layout.BodyAttrib + 1, -1, 1), float(Marks.UnixMicros)
            )
        )
        Results.append(TagAttrib(AttribLinks(-1, Layout.BodyAttrib, 1), (BodyTag,)))
    Results += [
        TagAttrib(
            AttribLinks(-1, -1, Layout.FaceBase + Index),
            (FeatureTag(FaceValue.Label, Operation),),
        )
        for Index, FaceValue in enumerate(Model.Faces)
        if FaceValue.Label
    ]
    Results += [
        TagAttrib(
            AttribLinks(-1, -1, Layout.EdgeBase + Index),
            (FeatureTag(EdgeValue.Label, Operation),),
        )
        for Index, EdgeValue in enumerate(Model.Edges)
        if EdgeValue.Label
    ]
    return tuple(Results)


def MakeCarriers(
    Model: FormBody, Links: FormLinks, Layout: NodeLayout
) -> tuple[int, ...]:
    Carriers = [-1] * Layout.EntityCount
    for FaceIndex in range(len(Model.Faces)):
        Carriers[Layout.SurfaceBase + FaceIndex] = FaceIndex
    for PcurveSlot, FaceIndex in enumerate(Links.PcurveFaces):
        Carriers[Layout.PcurveBase + PcurveSlot] = FaceIndex
    return tuple(Carriers)


def MakeFormNodes(
    Surface: TsplineSurface, Model: FormBody, Marks: FormMarks, IsHistory: bool
) -> FormDraft:
    Links = MakeFormLinks(Model)
    Layout = MakeNodeLayout(Model, Links, IsHistory)
    Entities = (
        *MakeShellNodes(Layout, IsHistory),
        *MakeFaceNodes(Model, Links, Layout),
        *MakeUseNodes(Model, Links, Layout),
        *MakeEdgeNodes(Model, Links, Layout),
        *MakeCurveNodes(Model, Links),
        *MakeTagNodes(Model, Layout, Marks),
    )
    if len(Entities) != Layout.EntityCount:
        raise ValueError("Converted Form BRep layout does not match its records")
    Scope = SubtransNode(Surface, Model.Regions)
    Surfaces = tuple(
        TsplineSurf(
            23100,
            FaceValue.Surface.Cache,
            0.0,
            FaceValue.Surface.Jumps,
            (1.0, 0.0, 1.0, 0.0),
            0,
            Scope,
            FaceValue.Surface.Region,
        )
        for FaceValue in Model.Faces
    )
    return FormDraft(Entities, MakeCarriers(Model, Links, Layout), Surfaces)
