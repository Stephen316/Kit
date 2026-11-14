from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.RelinkSubtypes import (
    RelinkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.SnapshotForm import SnapshotForm
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.formats.Fusion.BrepCodec.Journal.Validation.CountRoots import CountRoots


def EmitStateSmb(
    Model: JournalModel, StateId: int | None = None, *, Snapshot: bool = False
) -> bytes:
    if type(Snapshot) is not bool:
        raise ValueError("Fusion state snapshot form must be a boolean")
    Table = MakeLiveTable(Model, StateId)
    Ordinals = {Reference: Index for Index, Reference in enumerate(Table.LiveSlots)}
    Mapping = tuple(Ordinals.get(Reference, -1) for Reference in Table.SlotMap)
    Records = tuple(Table.Records[Reference] for Reference in Table.LiveSlots)
    if any(Record < 0 for Record in Records):
        raise ValueError("Fusion live state contains an absent revision")
    Entities = RelinkSubtypes(Model.Entities, Records)
    RootCount = 1 + CountRoots(Entities)
    if RootCount < 2:
        raise ValueError("Fusion standalone geometry requires a live body")
    Remapped = tuple(RemapEntity(Value, Mapping) for Value in Entities)
    Standalone = SnapshotForm(Remapped) if Snapshot else Remapped
    Parts = [EmitBrepHeader(Model.Stamp, RootCount, False, 10.0)]
    Parts.extend(EmitWireRecord(MakeEntityNode(Value)) for Value in Standalone)
    Parts.append(EncodeSmbName("End-of-ASM-data"))
    Payload = b"".join(Parts)
    if len(Payload) > 2 * 1024 * 1024:
        raise ValueError("Encoded Fusion state exceeds its byte quota")
    return Payload
