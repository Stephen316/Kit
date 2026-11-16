from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType

# the named kinds vocabulary must stay centralized so entity reconstruction agrees on supported native identities
KNamedKinds = {
    "IntrinsicMetaTypebool": WireType("bool"),
    "IntrinsicMetaTypeuint8": WireType("u8"),
    "IntrinsicMetaTypeuint16": WireType("u16"),
    "IntrinsicMetaTypeuint32": WireType("u32"),
    "IntrinsicMetaTypeuint64": WireType("u64"),
    "IntrinsicMetaTypeint32": WireType("i32"),
    "IntrinsicMetaTypefloat": WireType("f32"),
    "IntrinsicMetaTypedouble": WireType("f64"),
}
