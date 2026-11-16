from convert.Formats.Fusion.BrepCodec.History.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.Formats.Fusion.BrepCodec.Topology.HistoryRecords import BuildHistory
from convert.Formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepRows import EmitBrepRows
from convert.Formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# the history operation needs a consistent construction rule so topology identity survives native history reconstruction
def EmitHistory(
    Model: CylinderBody,
    Identity: BodyIdentity,
    TagSet: TopologyTags,
    History: HistoryState,
    Stamp: GeometryStamp,
    Vertices: VertexIndices | None = None,
    Tracking: EntityIds | None = None,
) -> bytes:
    Records = BuildHistory(Model, Identity, TagSet, Vertices, Tracking)
    CheckBrepRefs(Records, 2)
    return (
        EmitBrepHeader(Stamp, 2, True, 50.0)
        + EmitBrepRows(Records)
        + EmitJournal(History, len(Records))
    )
