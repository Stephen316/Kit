from convert.Formats.Fusion.SegmentCodec.Act.CheckActKey import CheckActKey
from convert.Formats.Fusion.SegmentCodec.Act.EmitActTokens import EmitActRolesMut
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink
from convert.Formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole


# a generated fields record ends at its reciprocal key without unexplained source data
def EmitActFields(KeyValue: str, Roles: tuple[tuple[ActRole, str], ...]) -> bytes:
    CheckActKey(KeyValue)
    SinkValue = MetaSink()
    SinkValue.AddBytes(bytes(6))
    EmitActRolesMut(SinkValue, Roles)
    SinkValue.AddText(KeyValue, WideText=True)
    return bytes(SinkValue.Buffer)
