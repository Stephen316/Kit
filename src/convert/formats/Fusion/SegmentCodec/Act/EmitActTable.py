from convert.formats.Fusion.SegmentCodec.Act.EmitActKeys import EmitActKeysMut
from convert.formats.Fusion.SegmentCodec.Act.EmitActTokens import (
    EmitActRolesMut,
    EmitActUuidMut,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole


# table payloads derive the wire layout from new route identities and change tokens
def EmitActTable(
    SnapshotId: str,
    HeadId: str,
    Routes: tuple[tuple[int, str], ...],
    Roles: tuple[tuple[ActRole, str], ...],
) -> bytes:
    SinkValue = MetaSink()
    SinkValue.AddText("ACTTable")
    SinkValue.AddBytes(bytes(2))
    EmitActKeysMut(SinkValue, Routes)
    EmitActUuidMut(SinkValue, SnapshotId)
    EmitActUuidMut(SinkValue, HeadId)
    SinkValue.AddWord(0)
    EmitActRolesMut(SinkValue, Roles)
    if (
        SnapshotId == HeadId
        or len(Roles) != len(ActRole)
        or not any(TokenText == HeadId for _, TokenText in Roles)
    ):
        raise ValueError("Invalid Fusion ACT table identifiers or roles")
    return bytes(SinkValue.Buffer)
