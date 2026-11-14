from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.BodyPlan import BodyPlan
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftKey import (
    KDraftNode,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftLoops import (
    DraftLoops,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftLookup import (
    DraftLookup,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import (
    FaceKey,
    FaceLabelOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceSurface import (
    FaceSurface,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LabelGroups import (
    LabelTags,
)


def DraftFaces(PlanValue: BodyPlan, FindIndex: DraftLookup) -> list[KDraftNode]:
    Ordinal = PlanValue.Ordinal
    Nodes: list[KDraftNode] = []
    Faces = PlanValue.Body.Faces
    for Index, FaceValue in enumerate(Faces):
        KeyValue = FaceKey(FaceValue)
        FaceRef, TagRef, SurfRef = (
            ("face", Ordinal, KeyValue),
            ("ftag", Ordinal, KeyValue),
            ("surf", Ordinal, KeyValue),
        )
        Following = (
            FindIndex(("face", Ordinal, FaceKey(Faces[Index + 1])))
            if Index + 1 < len(Faces)
            else -1
        )
        Surface, Reversed = FaceSurface(FaceValue)
        Groups = LabelTags(FaceLabelOf(FaceValue))
        Tracked = dict(PlanValue.Body.Tracks).get(FaceLabelOf(FaceValue))
        TrackRef = ("ftrack", Ordinal, KeyValue)
        Leading = TagRef if Tracked is None else TrackRef
        Prefix = EntityPrefix(FindIndex(Leading), PlanValue.FaceTags[KeyValue])
        First = FindIndex(("loop", Ordinal, KeyValue, 0))
        Nodes.append(
            (
                FaceRef,
                FaceNode(
                    Prefix,
                    Following,
                    First,
                    FindIndex(("shell", Ordinal)),
                    FindIndex(SurfRef),
                    Reversed,
                    False,
                    None,
                ),
            )
        )
        Owner = FindIndex(FaceRef)
        if Tracked is not None:
            Links = AttribLinks(FindIndex(TagRef), -1, Owner)
            Nodes.append((TrackRef, TrackAttrib(Links, Tracked)))
        Prior = -1 if Tracked is None else FindIndex(TrackRef)
        Nodes.append((TagRef, TagAttrib(AttribLinks(-1, Prior, Owner), Groups)))
        Nodes.append((SurfRef, Surface))
        Nodes.extend(DraftLoops(PlanValue, FaceValue, FindIndex))
    return Nodes
