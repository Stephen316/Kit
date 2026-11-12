from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActFields import (
    KActFieldsGuid,
    ReadActFields,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRoute import ActRoute


# a bijective fields inventory blocks duplicate or unindexed evidence
def ReadActRoutes(
    ActData: bytes,
    ActSpans: tuple[RecordSpan, ...],
    Entries: tuple[tuple[int, str, int, int], ...],
) -> tuple[ActRoute, ...]:
    Fields: dict[int, RecordSpan] = {}
    for FieldSpan in ActSpans:
        if FieldSpan.ClassGuid != KActFieldsGuid:
            continue
        if FieldSpan.ObjectId in Fields:
            raise ValueError("Duplicate Fusion ACT fields identity")
        Fields[FieldSpan.ObjectId] = FieldSpan
    if len(Fields) != len(Entries):
        raise ValueError("Fusion ACT table and fields inventory disagree")
    Routes: list[ActRoute] = []
    for FieldsId, KeyValue, Prefix, OwnerId in Entries:
        EntrySpan = Fields.pop(FieldsId, None)
        if EntrySpan is None:
            raise ValueError("Missing or duplicate Fusion ACT fields reference")
        Roles, Residual = ReadActFields(ActData, EntrySpan, KeyValue)
        Routes.append(ActRoute(KeyValue, Prefix, OwnerId, EntrySpan, Roles, Residual))
    return tuple(Routes)
