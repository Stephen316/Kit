from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.FormulaDeps.ScopedParams import ReadPartScope
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SegmentCodec.Parameters.ParamScope import ParamScope
from convert.formats.Fusion.Topology.BodyScope import FindBodyScope
from convert.formats.Fusion.ZipHistory import ReadBulkHistory


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
