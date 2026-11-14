from enum import StrEnum


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
