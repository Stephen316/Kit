from functools import cache as MakeCache

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import AsRecords
from convert.formats.Fusion.DrawingCodec.Dwg.Records.ParseSpec import ParseSpec
from convert.formats.Fusion.DrawingCodec.Dwg.Records.PutRecordMut import (
    PutValueMut,
    TakeFieldMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.ReadRecordMut import (
    KMaxRepeat,
    ReadValueMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.RecordSinks import RecordSinks
from convert.formats.Fusion.DrawingCodec.Dwg.Records.RecordStreams import (
    RecordStreams,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecOp import SpecOp
from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecScope import (
    KBranchKinds,
    KScopes,
    IsBranchTrue,
    LookupCount,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.LocalKinds import (
    KLocalPuts,
    KLocalReads,
)


@MakeCache
def CachedSpec(SpecText: str) -> tuple[SpecOp, ...]:
    return ParseSpec(SpecText)


def ReadWalk(
    SpecOps: tuple[SpecOp, ...], Streams: RecordStreams, Scopes: KScopes
) -> DwgRecord:
    Fields: list[DwgField] = []
    ReadStepsMut(SpecOps, Streams, Fields, Scopes)
    return DwgRecord(tuple(Fields))


def ReadStepsMut(
    SpecOps: tuple[SpecOp, ...],
    Streams: RecordStreams,
    Fields: list[DwgField],
    Scopes: KScopes,
) -> None:
    Inner = (Fields, *Scopes)
    for Operation in SpecOps:
        if Operation.OpKind in KBranchKinds:
            IsTaken = IsBranchTrue(Operation, Inner, Streams.VersionText)
            Chosen = Operation.BodyOps if IsTaken else Operation.ElseOps
            ReadStepsMut(Chosen, Streams, Fields, Scopes)
        elif Operation.OpKind == "each":
            Count = LookupCount(Operation.OpArgs[0], Inner)
            if Count > KMaxRepeat:
                raise ValueError("DWG section repeat count exceeds the safety bound")
            Items = tuple(
                ReadWalk(Operation.BodyOps, Streams, Inner) for _ in range(Count)
            )
            Fields.append(DwgField(Operation.OpName, Items))
        else:
            Reader = KLocalReads.get(Operation.OpKind)
            Value = (
                ReadValueMut(Operation, Streams, Inner)
                if Reader is None
                else Reader(Streams.DataCursor)
            )
            Fields.append(DwgField(Operation.OpName, Value))


def PutWalkMut(
    SpecOps: tuple[SpecOp, ...], Record: DwgRecord, Sinks: RecordSinks, Scopes: KScopes
) -> None:
    Pending = list(reversed(Record.RecordFields))
    Written: list[DwgField] = []
    PutStepsMut(SpecOps, Pending, Written, Sinks, Scopes)
    if Pending:
        raise ValueError(
            f"DWG section field {Pending[-1].FieldName!r} is not in its spec"
        )


def PutStepsMut(
    SpecOps: tuple[SpecOp, ...],
    Pending: list[DwgField],
    Written: list[DwgField],
    Sinks: RecordSinks,
    Scopes: KScopes,
) -> None:
    Inner = (Written, *Scopes)
    for Operation in SpecOps:
        if Operation.OpKind in KBranchKinds:
            IsTaken = IsBranchTrue(Operation, Inner, Sinks.VersionText)
            Chosen = Operation.BodyOps if IsTaken else Operation.ElseOps
            PutStepsMut(Chosen, Pending, Written, Sinks, Scopes)
            continue
        Entry = TakeFieldMut(Pending, Operation.OpName)
        Putter = KLocalPuts.get(Operation.OpKind)
        if Operation.OpKind == "each":
            Items = AsRecords(Entry.FieldValue)
            if len(Items) != LookupCount(Operation.OpArgs[0], Inner):
                raise ValueError(f"DWG section list {Entry.FieldName!r} size mismatch")
            for ItemRecord in Items:
                PutWalkMut(Operation.BodyOps, ItemRecord, Sinks, Inner)
        elif Putter is not None:
            Putter(Sinks.DataWriter, Entry.FieldValue)
        else:
            PutValueMut(Operation, Entry.FieldValue, Sinks, Inner)
        Written.append(Entry)
