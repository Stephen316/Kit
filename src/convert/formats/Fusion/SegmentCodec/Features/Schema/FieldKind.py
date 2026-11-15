from enum import StrEnum


# the field kind contract needs a dedicated boundary so native records retain their segment ownership and schema
class FieldKind(StrEnum):
    KBoolean = "bool"
    KUnsigned = "uint32"
    KInteger = "int32"
    KIdentity = "uint64"
    KDecimal = "double"
    KUnicode = "wstring"
    KUuidText = "uuid"
    KVector = "vector3d"
    KStrongRef = "strongref"
    KPassiveRef = "passiveref"
    KStrongVector = "strongvector"
    KPassiveVector = "passivevector"
    KPassiveList = "passivelist"
    KStrongSet = "strongset"
