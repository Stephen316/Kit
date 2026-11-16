from convert.Formats.Fusion.Assembly.ComponentRead import KComponentGuid
from convert.Formats.Fusion.Assembly.OccurrenceRead import KOccurrenceGuid
from convert.Formats.Fusion.FormulaDeps.ParamCollection import (
    KParamCollection,
    ReadMemberOrder,
)
from convert.Formats.Fusion.FormulaDeps.ParamRegistry import (
    KParamRegistry,
    ReadNameTable,
)
from convert.Formats.Fusion.HistoryPart import HistoryPart
from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.NativeHistory import KHistoryGuid
from convert.Formats.Fusion.NumericParam import KParamGuid
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Topology.BodyScope import FindBodyScope


# member records must link back to the collection that makes their names visible
def CheckMemberRefs(
    BulkData: bytes,
    Primary: dict[int, RecordSpan],
    Members: frozenset[int],
    CollectionId: int,
) -> None:
    for MemberId in Members:
        SpanValue = Primary.get(MemberId)
        if (
            SpanValue is None
            or SpanValue.ClassGuid != KParamGuid
            or SpanValue.EndOffset - SpanValue.PayloadOffset < 16
        ):
            raise ValueError("Unknown Fusion parameter collection member")
        Cursor = MetaCursor(BulkData[SpanValue.EndOffset - 12 : SpanValue.EndOffset])
        if Cursor.TakeBytes(1) != b"\0" or ReadNativeRef(Cursor) != CollectionId:
            raise ValueError("Fusion parameter collection member does not reciprocate")


# explicit history selection cannot grant standalone visibility inside an assembly
def ReadPartScope(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
    *,
    VerifyOrder: bool = False,
) -> tuple[
    dict[int, RecordSpan], RecordSpan, RecordSpan, tuple[int, ...], dict[int, str]
]:
    Records = tuple(SpanValue for SpanValue in Spans if SpanValue.IsPrimary)
    Primary = {SpanValue.ObjectId: SpanValue for SpanValue in Records}
    if (
        len(Primary) != len(Records)
        or sum(SpanValue.ClassGuid == KComponentGuid for SpanValue in Records) != 1
        or sum(SpanValue.ClassGuid == KOccurrenceGuid for SpanValue in Spans) != 1
        or tuple(
            SpanValue.ObjectId
            for SpanValue in Records
            if SpanValue.ClassGuid == KHistoryGuid
        )
        != (History.HistoryId,)
    ):
        raise ValueError("Fusion formula visibility is not a standalone part")
    Collections = tuple(
        SpanValue for SpanValue in Records if SpanValue.ClassGuid == KParamCollection
    )
    ComponentId = FindBodyScope(BulkData, Spans, History)
    if ComponentId is None or len(Collections) != 1:
        raise ValueError("Fusion part parameter collection is unresolved")
    Collection = Collections[0]
    RegistryId, Order = ReadMemberOrder(
        BulkData[Collection.PayloadOffset + 4 : Collection.EndOffset],
        ComponentId,
        VerifyOrder=VerifyOrder,
    )
    Registry = Primary.get(RegistryId)
    if Registry is None or Registry.ClassGuid != KParamRegistry:
        raise ValueError("Fusion parameter name registry is unresolved")
    Members = frozenset(Order)
    CheckMemberRefs(BulkData, Primary, Members, Collection.ObjectId)
    Names = ReadNameTable(
        BulkData[Registry.PayloadOffset + 4 : Registry.EndOffset],
        Collection.ObjectId,
        Members,
        MemberOrder=Order if VerifyOrder else None,
    )
    return Primary, Collection, Registry, Order, Names


# ordinary formula projection only needs the validated standalone name map
def ReadPartNames(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], History: HistoryPart
) -> dict[int, str]:
    return ReadPartScope(BulkData, Spans, History)[-1]
