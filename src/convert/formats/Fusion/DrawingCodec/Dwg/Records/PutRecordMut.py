from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutCodeMut import PutDefDblMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutRawMut import (
    PutBytesMut,
    PutRawCharMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
    KDwgValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsBytes,
    AsFloat,
    AsHandle,
    AsHandles,
    AsInt,
    AsPoint,
    AsRecord,
    AsRecords,
    AsText,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CountedKinds import (
    EncodeCounted,
    KCountedReads,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.PutCodes import KPutCodes
from convert.formats.Fusion.DrawingCodec.Dwg.Records.RecordSinks import RecordSinks
from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecOp import SpecOp
from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecScope import (
    KBranchKinds,
    KScopes,
    IsBranchTrue,
    LookupCount,
    LookupFloat,
    LookupValue,
)


def PutRecordMut(
    SpecOps: tuple[SpecOp, ...], Record: DwgRecord, Sinks: RecordSinks, Scopes: KScopes
) -> None:
    Pending = list(reversed(Record.RecordFields))
    Written: list[DwgField] = []
    PutOpsMut(SpecOps, Pending, Written, Sinks, Scopes)
    if Pending:
        raise ValueError(
            f"DWG record field {Pending[-1].FieldName!r} is not in its spec"
        )


def TakeFieldMut(Pending: list[DwgField], FieldName: str) -> DwgField:
    if not Pending or Pending[-1].FieldName != FieldName:
        raise ValueError(f"DWG record lacks field {FieldName!r} at its spec position")
    return Pending.pop()


def PutOpsMut(
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
            PutOpsMut(Chosen, Pending, Written, Sinks, Scopes)
            continue
        Entry = TakeFieldMut(Pending, Operation.OpName)
        if Operation.OpKind == "each":
            Items = AsRecords(Entry.FieldValue)
            if len(Items) != LookupCount(Operation.OpArgs[0], Inner):
                raise ValueError(f"DWG record list {Entry.FieldName!r} size mismatch")
            for ItemRecord in Items:
                PutRecordMut(Operation.BodyOps, ItemRecord, Sinks, Inner)
        elif Operation.OpKind == "nest":
            PutRecordMut(Operation.BodyOps, AsRecord(Entry.FieldValue), Sinks, Inner)
        elif Operation.OpKind == "zip":
            PutPairedMut(Operation, AsRecords(Entry.FieldValue), Sinks, Inner)
        else:
            PutValueMut(Operation, Entry.FieldValue, Sinks, Inner)
        Written.append(Entry)


def PutPairedMut(
    Operation: SpecOp,
    Items: tuple[DwgRecord, ...],
    Sinks: RecordSinks,
    Scopes: KScopes,
) -> None:
    Partners = AsRecords(LookupValue(Operation.OpArgs[0], Scopes))
    if len(Items) != len(Partners):
        raise ValueError(f"DWG record list {Operation.OpName!r} size mismatch")
    for ItemRecord, Partner in zip(Items, Partners, strict=True):
        PartnerScope = (list(Partner.RecordFields), *Scopes)
        PutRecordMut(Operation.BodyOps, ItemRecord, Sinks, PartnerScope)


def PutValueMut(
    Operation: SpecOp, Value: KDwgValue, Sinks: RecordSinks, Scopes: KScopes
) -> None:
    KindText = Operation.OpKind
    Putter = KPutCodes.get(KindText)
    if Putter is not None:
        Putter(Sinks.DataWriter, Value)
    elif KindText == "TU":
        Sinks.TextItems.append(AsText(Value))
    elif KindText == "H":
        Sinks.HandleRefs.append(AsHandle(Value))
    elif KindText in ("Hs", "HRest"):
        Handles = AsHandles(Value)
        if KindText == "Hs" and len(Handles) != LookupCount(
            Operation.OpArgs[0], Scopes
        ):
            raise ValueError("DWG record handle list size mismatch")
        Sinks.HandleRefs.extend(Handles)
    elif KindText == "DD":
        Default = LookupFloat(Operation.OpArgs[0], Scopes)
        PutDefDblMut(Sinks.DataWriter, AsFloat(Value), Default)
    elif KindText == "2DD":
        Defaults = AsPoint(LookupValue(Operation.OpArgs[0], Scopes), 2)
        for Coordinate, Default in zip(AsPoint(Value, 2), Defaults, strict=True):
            PutDefDblMut(Sinks.DataWriter, Coordinate, Default)
    else:
        PutBulkMut(Operation, Value, Sinks, Scopes)


def PutBulkMut(
    Operation: SpecOp, Value: KDwgValue, Sinks: RecordSinks, Scopes: KScopes
) -> None:
    if Operation.OpKind in KCountedReads:
        ByteCount = LookupCount(Operation.OpArgs[0], Scopes)
        DataValue = EncodeCounted(Operation.OpKind, Value, ByteCount)
        PutBytesMut(Sinks.DataWriter, DataValue)
    elif Operation.OpKind == "Bits":
        Width = LookupCount(Operation.OpArgs[0], Scopes)
        Sinks.DataWriter.PutBits(AsInt(Value), Width)
    elif Operation.OpKind == "Zeros":
        DataValue = AsBytes(Value)
        if 0 in DataValue:
            raise ValueError("DWG record zero terminated bytes contain a zero")
        PutBytesMut(Sinks.DataWriter, DataValue)
        PutRawCharMut(Sinks.DataWriter, 0)
    elif Operation.OpKind == "Rest":
        Fields = AsRecord(Value).RecordFields
        if [Entry.FieldName for Entry in Fields] != ["Width", "Bits"]:
            raise ValueError("DWG record rest field is malformed")
        Sinks.DataWriter.PutBits(
            AsInt(Fields[1].FieldValue), AsInt(Fields[0].FieldValue)
        )
    else:
        raise ValueError(f"DWG record spec kind {Operation.OpKind!r} is unsupported")
