from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.BodyPlan import BodyPlan
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftKey import (
    KDraftNode,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftLookup import (
    DraftLookup,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import FaceKey
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.SketchCurve import (
    SketchCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import KShapeFace


def DraftLoops(
    PlanValue: BodyPlan, FaceValue: KShapeFace, FindIndex: DraftLookup
) -> list[KDraftNode]:
    Ordinal, KeyValue = PlanValue.Ordinal, FaceKey(FaceValue)
    Nodes: list[KDraftNode] = []
    for LoopIndex, LoopValue in enumerate(FaceValue.Loops):
        LoopRef = ("loop", Ordinal, KeyValue, LoopIndex)
        Following = (
            FindIndex(("loop", Ordinal, KeyValue, LoopIndex + 1))
            if LoopIndex + 1 < len(FaceValue.Loops)
            else -1
        )
        RefList = [("use", Ordinal, KeyValue, UseValue.Edge) for UseValue in LoopValue]
        Nodes.append(
            (
                LoopRef,
                LoopNode(
                    EntityPrefix(-1, -1),
                    Following,
                    FindIndex(RefList[0]),
                    FindIndex(("face", Ordinal, KeyValue)),
                ),
            )
        )
        for Index, UseValue in enumerate(LoopValue):
            Curve = SketchCurve(PlanValue.Body, FaceValue, UseValue.Edge)
            Attrib = ("skat", Ordinal, KeyValue, UseValue.Edge)
            Prefix = EntityPrefix(-1 if Curve is None else FindIndex(Attrib), -1)
            NodeValue = CoedgeNode(
                Prefix,
                FindIndex(RefList[(Index + 1) % len(RefList)]),
                FindIndex(RefList[Index - 1]),
                FindIndex(PlanValue.Partners[RefList[Index]]),
                FindIndex(("edge", Ordinal, UseValue.Edge)),
                not UseValue.Forward,
                FindIndex(LoopRef),
            )
            Nodes.append((RefList[Index], NodeValue))
            if Curve is not None:
                LinkValue = SketchLink(Curve, 0, 0, 1, 1)
                Nodes.append(
                    (
                        Attrib,
                        SketchAttrib(
                            AttribLinks(-1, -1, FindIndex(RefList[Index])), LinkValue
                        ),
                    )
                )
    return Nodes
