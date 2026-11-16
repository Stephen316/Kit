from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.BodyPlan import BodyPlan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.DraftKey import (
    KDraftNode,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.DraftLookup import (
    DraftLookup,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import FaceKey
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.LabelGroups import (
    LabelTags,
)


# the draft frame contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def DraftFrame(PlanValue: BodyPlan, FindIndex: DraftLookup) -> list[KDraftNode]:
    Ordinal = PlanValue.Ordinal
    Label = PlanValue.Body.BodyLabel
    BodyValue, TimeValue, TagValue = (
        ("body", Ordinal),
        ("btime", Ordinal),
        ("btag", Ordinal),
    )
    LumpValue, Shell = ("lump", Ordinal), ("shell", Ordinal)
    First = ("face", Ordinal, FaceKey(PlanValue.Body.Faces[0]))
    return [
        (
            BodyValue,
            BodyNode(
                EntityPrefix(FindIndex(TimeValue), PlanValue.BodyTag),
                FindIndex(LumpValue),
            ),
        ),
        (
            TimeValue,
            TimeAttrib(
                AttribLinks(FindIndex(TagValue), -1, FindIndex(BodyValue)),
                PlanValue.UnixMicros,
            ),
        ),
        (
            LumpValue,
            LumpNode(EntityPrefix(-1, -1), -1, FindIndex(Shell), FindIndex(BodyValue)),
        ),
        (
            TagValue,
            TagAttrib(
                AttribLinks(-1, FindIndex(TimeValue), FindIndex(BodyValue)),
                LabelTags(Label),
            ),
        ),
        (
            Shell,
            ShellNode(EntityPrefix(-1, -1), -1, FindIndex(First), FindIndex(LumpValue)),
        ),
    ]
