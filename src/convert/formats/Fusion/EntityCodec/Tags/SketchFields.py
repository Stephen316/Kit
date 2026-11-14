from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType

KSketchFields = (
    FieldSpec("version", WireType("i32", AllowedInts=(3,))),
    FieldSpec("tagId", WireType("u64")),
    FieldSpec("secondaryTagId", WireType("u64")),
    FieldSpec("direction", WireType("u32", AllowedInts=(0, 1, 0xFFFFFFFF))),
    FieldSpec("splitSequenceId", WireType("u32")),
    FieldSpec("splitTotalNumber", WireType("u32")),
    FieldSpec("topologyRoleFlags", WireType("u64", AllowedInts=(0,))),
)
