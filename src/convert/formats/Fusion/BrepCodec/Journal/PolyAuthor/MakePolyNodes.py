from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.MakePolyEdges import (
    MakePolyEdges,
    MakePolyCurves,
)
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.MakePolyFaces import (
    MakePolyFaces,
    MakePolyLoops,
    MakePolyPlanes,
)
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.MakePolyPoints import (
    MakePolyPoints,
    MakePolyVerts,
)
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.MakePolyUses import (
    MakePolyUses,
)
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.PolyLayout import PolyLayout


def MakePolyNodes(
    Layout: PolyLayout, EntityTag: int, Placement: TransformNode | None
) -> tuple[KJournalEntity, ...]:
    Prefix = EntityPrefix(-1, -1)
    Coedges = MakePolyUses(Layout)
    TransformRef = Layout.CurveBase + len(Layout.Edges) if Placement is not None else -1
    Records: tuple[KJournalEntity, ...] = (
        AsmRoot(-1, -1, "232.5.0.65535"),
        BodyNode(EntityPrefix(-1, EntityTag), 2, TransformRef),
        LumpNode(Prefix, -1, 3, 1),
        ShellNode(Prefix, -1, 4, 2),
        *MakePolyFaces(Layout),
        *MakePolyLoops(Layout),
        *Coedges,
        *MakePolyEdges(Layout, Coedges),
        *MakePolyVerts(Layout),
        *MakePolyPoints(Layout),
        *MakePolyPlanes(Layout),
        *MakePolyCurves(Layout),
    )
    return Records if Placement is None else (*Records, Placement)
