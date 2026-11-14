from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalEntities,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.CheckComplex import (
    CheckComplex,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.CheckSubtypes import (
    CheckSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeomTags import (
    CheckGeomTags,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckLiveRefs import (
    CheckLiveRefs,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckNode import CheckNode
from convert.formats.Fusion.BrepCodec.Journal.Validation.CountRoots import CountRoots
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckModelHead import (
    CheckModelHead,
)


def CheckGeometry(Model: GeometryState) -> None:
    CheckModelHead(Model.Header, False)
    if (
        type(Model.Entities) is not tuple
        or not 2 <= len(Model.Entities) <= KJournalEntities
    ):
        raise ValueError("Invalid Fusion geometry table size or mutability")
    if (
        not isinstance(Model.Entities[0], AsmRoot)
        or sum(isinstance(Value, AsmRoot) for Value in Model.Entities) != 1
    ):
        raise ValueError("Fusion geometry requires one leading ASM header")
    if CountRoots(Model.Entities) != Model.Header.RootCount - 1:
        raise ValueError("Fusion geometry bodies disagree with its root count")
    for Value in Model.Entities:
        CheckNode(Value)
    CheckGeomTags(Model)
    CheckSubtypes(Model.Entities)
    CheckComplex(Model.Entities)
    Records = tuple(MakeEntityNode(Value) for Value in Model.Entities)
    Slots = tuple(range(len(Records)))
    CheckLiveRefs(
        Records, {Index: Index for Index in Slots}, Slots, Model.Header.RootCount
    )
