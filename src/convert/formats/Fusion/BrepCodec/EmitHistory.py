from convert.formats.Fusion.BrepCodec.History.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.formats.Fusion.BrepCodec.Topology.HistoryRecords import BuildHistory
from convert.formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepRows import EmitBrepRows
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


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
