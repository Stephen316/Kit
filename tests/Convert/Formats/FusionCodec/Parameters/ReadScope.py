from struct import unpack_from as UnpackFrom

from convert.Formats.Fusion.FormulaDeps.ScopedParams import ReadPartScope
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SegmentCodec.Parameters.ParamScope import ParamScope
from convert.Formats.Fusion.Topology.BodyScope import FindBodyScope
from convert.Formats.Fusion.ZipHistory import ReadBulkHistory


# shared read scope setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadScope(BulkData: bytes, Spans: tuple[RecordSpan, ...]) -> ParamScope:
    Histories, _, _ = ReadBulkHistory(BulkData, Spans)
    (History,) = Histories
    _, Collection, Registry, Members, Names = ReadPartScope(BulkData, Spans, History)
    ComponentId = FindBodyScope(BulkData, Spans, History)
    assert ComponentId is not None
    return ParamScope(
        Collection.ObjectId,
        Registry.ObjectId,
        ComponentId,
        int(UnpackFrom("<I", BulkData, Collection.PayloadOffset + 15)[0]),
        Members,
        tuple(Names.items()),
    )
