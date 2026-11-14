from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadCodeMut import ReadDefDblMut
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
    KDwgValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsPoint,
    AsRecords,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CountedKinds import KCountedReads
from convert.formats.Fusion.DrawingCodec.Dwg.Records.ReadCodes import KReadCodes
from convert.formats.Fusion.DrawingCodec.Dwg.Records.RecordStreams import (
    RecordStreams,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecOp import SpecOp
from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecScope import (
    KBranchKinds,
    KScopes,
    IsBranchTrue,
    LookupCount,
    LookupFloat,
    LookupValue,
)

KMaxRepeat = 1 << 20


def ReadRecordMut(
    SpecOps: tuple[SpecOp, ...], Streams: RecordStreams, Scopes: KScopes
) -> DwgRecord:
    Fields: list[DwgField] = []
    ReadOpsMut(SpecOps, Streams, Fields, Scopes)
    return DwgRecord(tuple(Fields))


def ReadOpsMut(
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
            ReadOpsMut(Chosen, Streams, Fields, Scopes)
        elif Operation.OpKind == "each":
            Count = LookupCount(Operation.OpArgs[0], Inner)
            if Count > KMaxRepeat:
                raise ValueError("DWG record repeat count exceeds the safety bound")
            Items = tuple(
                ReadRecordMut(Operation.BodyOps, Streams, Inner) for _ in range(Count)
            )
            Fields.append(DwgField(Operation.OpName, Items))
        elif Operation.OpKind == "nest":
            Nested = ReadRecordMut(Operation.BodyOps, Streams, Inner)
            Fields.append(DwgField(Operation.OpName, Nested))
        elif Operation.OpKind == "zip":
            Paired = ReadPairedMut(Operation, Streams, Inner)
            Fields.append(DwgField(Operation.OpName, Paired))
        else:
            Value = ReadValueMut(Operation, Streams, Inner)
            Fields.append(DwgField(Operation.OpName, Value))


def ReadPairedMut(
    Operation: SpecOp, Streams: RecordStreams, Scopes: KScopes
) -> tuple[DwgRecord, ...]:
    Partners = AsRecords(LookupValue(Operation.OpArgs[0], Scopes))
    return tuple(
        ReadRecordMut(Operation.BodyOps, Streams, (list(Partner.RecordFields), *Scopes))
        for Partner in Partners
    )


def ReadValueMut(
    Operation: SpecOp, Streams: RecordStreams, Scopes: KScopes
) -> KDwgValue:
    KindText = Operation.OpKind
    Cursor = Streams.DataCursor
    Reader = KReadCodes.get(KindText)
    if Reader is not None:
        return Reader(Cursor)
    if KindText == "TU":
        return Streams.TakeText()
    if KindText == "H":
        return Streams.TakeHandle()
    if KindText == "Hs":
        Count = LookupCount(Operation.OpArgs[0], Scopes)
        return tuple(Streams.TakeHandle() for _ in range(Count))
    if KindText == "HRest":
        return Streams.TakeHandles()
    if KindText == "DD":
        return ReadDefDblMut(Cursor, LookupFloat(Operation.OpArgs[0], Scopes))
    if KindText == "2DD":
        return ReadPairMut(Streams, Operation.OpArgs[0], Scopes)
    return ReadBulkMut(Operation, Streams, Scopes)


def ReadPairMut(Streams: RecordStreams, BaseName: str, Scopes: KScopes) -> KDwgValue:
    Defaults = AsPoint(LookupValue(BaseName, Scopes), 2)
    return tuple(ReadDefDblMut(Streams.DataCursor, Default) for Default in Defaults)


def ReadBulkMut(
    Operation: SpecOp, Streams: RecordStreams, Scopes: KScopes
) -> KDwgValue:
    Cursor = Streams.DataCursor
    Decoder = KCountedReads.get(Operation.OpKind)
    if Decoder is not None:
        Count = LookupCount(Operation.OpArgs[0], Scopes)
        return Decoder(Cursor.TakeBits(8 * Count).to_bytes(Count, "big"))
    if Operation.OpKind == "Bits":
        return Cursor.TakeBits(LookupCount(Operation.OpArgs[0], Scopes))
    if Operation.OpKind == "Zeros":
        Output = bytearray()
        while (ByteValue := Cursor.TakeBits(8)) != 0:
            Output.append(ByteValue)
        return bytes(Output)
    if Operation.OpKind == "Rest":
        Width = Cursor.Limit - Cursor.Position
        BitValue = Cursor.TakeBits(Width)
        return DwgRecord((DwgField("Width", Width), DwgField("Bits", BitValue)))
    raise ValueError(f"DWG record spec kind {Operation.OpKind!r} is unsupported")
