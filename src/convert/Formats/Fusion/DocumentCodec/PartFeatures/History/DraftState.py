from convert.Formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.BodyPlan import BodyPlan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.DraftEdges import (
    DraftEdges,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.DraftFaces import (
    DraftFaces,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.DraftFrame import (
    DraftFrame,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.DraftKey import (
    KDraftNode,
    KDraftState,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.DraftLookup import (
    DraftLookup,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.LedgerTags import (
    LedgerTags,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.PlanBody import PlanBody
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.TagLedger import (
    TagLedger,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody

# kernel version must remain consistent across callers so feature parameters remain connected to the resulting geometry
KKernelVersion = "232.5.0.65535"


# the draft nodes contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def DraftNodes(Plans: list[BodyPlan], FindIndex: DraftLookup) -> list[KDraftNode]:
    Nodes: list[KDraftNode] = [(("root",), AsmRoot(-1, -1, KKernelVersion))]
    Frames = [DraftFrame(PlanValue, FindIndex) for PlanValue in Plans]
    Nodes.extend(Frame[0] for Frame in Frames)
    for Frame in Frames:
        Nodes.extend(Frame[1:])
    for PlanValue in Plans:
        Nodes.extend(DraftFaces(PlanValue, FindIndex))
        Nodes.extend(DraftEdges(PlanValue, FindIndex))
    return Nodes


# draft state needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
def DraftState(
    Bodies: tuple[ShapeBody, ...], Ledger: TagLedger, UnixMicros: float
) -> KDraftState:

    # ordering by body value ordinal must stay deterministic so parametric feature reconstruction resolves equivalent inputs consistently
    Ordered = tuple(sorted(Bodies, key=lambda BodyValue: BodyValue.Ordinal))
    Plans = [
        PlanBody(BodyValue, BodyValue.Ordinal, FaceTags, BodyTag, UnixMicros)
        for BodyValue, (FaceTags, BodyTag) in zip(
            Ordered, LedgerTags(Ordered, Ledger), strict=True
        )
    ]
    KeyList = [NodeValue[0] for NodeValue in DraftNodes(Plans, DraftLookup(None))]
    Indices = {KeyValue: Index for Index, KeyValue in enumerate(KeyList)}
    if len(Indices) != len(KeyList):
        raise ValueError("Fusion part journal draft repeats a node identity")
    return tuple(DraftNodes(Plans, DraftLookup(Indices)))
