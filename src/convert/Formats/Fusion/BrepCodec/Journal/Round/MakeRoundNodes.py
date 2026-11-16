from convert.Formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Round.MakeRoundSurf import MakeRoundSurf
from convert.Formats.Fusion.BrepCodec.Journal.Round.SphereBody import SphereBody
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusBody import TorusBody


# the round nodes operation needs a consistent construction rule so topology changes retain their native revision relationships
def MakeRoundNodes(Model: SphereBody | TorusBody) -> tuple[KJournalEntity, ...]:
    Prefix = EntityPrefix(-1, -1)
    return (
        AsmRoot(-1, -1, "232.5.0.65535"),
        BodyNode(EntityPrefix(-1, Model.EntityTag), 2),
        LumpNode(Prefix, -1, 3, 1),
        ShellNode(Prefix, -1, 4, 2),
        FaceNode(Prefix, -1, -1, 3, 5, False, False, None),
        MakeRoundSurf(Model),
    )
