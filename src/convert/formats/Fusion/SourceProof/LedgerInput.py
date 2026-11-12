from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.NativeHistory import KHistoryGuid
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.ProofClaim import ProofScope

# these stream entries define the physical extent and ownership of the design census
KDesignStreams = frozenset(
    (KDesignPrefix + "BulkStream.dat", KDesignPrefix + "MetaStream.dat")
)


# an empty or ambiguous central directory cannot support coverage closure
def IndexMembers(
    Members: tuple[ArchiveMember, ...],
) -> dict[str, ArchiveMember]:
    Result = {Value.Name: Value for Value in Members}
    if (
        len(Result) != len(Members)
        or len({Value.HeaderOffset for Value in Members}) != len(Members)
        or not KDesignStreams <= Result.keys()
        or any(Result[NameValue].IsDirectory for NameValue in KDesignStreams)
    ):
        raise ValueError(
            "Fusion source proof archive census is incomplete or ambiguous"
        )
    return Result


# offsets and primary ownership prevent omitted spans from masquerading as coverage
def IndexSpans(
    Spans: tuple[RecordSpan, ...], BulkSize: int, Scope: ProofScope
) -> dict[int, RecordSpan]:
    Primary: dict[int, RecordSpan] = {}
    Result: dict[int, RecordSpan] = {}
    PreviousEnd = 0
    for Value in sorted(Spans, key=SpanOffset):
        if (
            Value.StartOffset != PreviousEnd
            or not Value.StartOffset < Value.PayloadOffset <= Value.EndOffset
            or Value.EndOffset > BulkSize
            or (Value.IsPrimary and Value.ObjectId in Primary)
        ):
            raise ValueError(
                "Fusion source proof record census is incomplete or ambiguous"
            )
        PreviousEnd = Value.EndOffset
        Result[Value.StartOffset] = Value
        if Value.IsPrimary:
            Primary[Value.ObjectId] = Value
    History = Primary.get(Scope.HistoryId)
    if (
        PreviousEnd != BulkSize
        or any(Value.ObjectId not in Primary for Value in Spans)
        or History is None
        or History.ClassGuid != KHistoryGuid
        or Scope.OwnerId not in Primary
    ):
        raise ValueError(
            "Fusion source proof record census or selected history disagrees"
        )
    return Result


# record order follows actual storage offsets independently of supplied claim ordering
def SpanOffset(Value: RecordSpan) -> int:
    return Value.StartOffset
