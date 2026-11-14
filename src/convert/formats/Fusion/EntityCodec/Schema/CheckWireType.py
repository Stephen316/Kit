from convert.formats.Fusion.EntityCodec.Limits import KMaxCount, KMaxDepth
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.CheckFlag import CheckFlag

KTypeArguments = {
    "sequence": 1,
    "set": 1,
    "optional": 1,
    "fixed": 1,
    "map": 2,
    "pair": 2,
    "ge-array": 1,
}
KLeafKinds = frozenset(
    (
        "bool",
        "u8",
        "u16",
        "u32",
        "u64",
        "i32",
        "f32",
        "f64",
        "ascii",
        "utf16",
        "ref",
        "struct",
        "object",
        "matrix",
        "unsupported",
        "recipe",
        "sketch-tag",
    )
)


def CheckWireType(Shape: WireType, Catalog: EntityCatalog, Depth: int = 0) -> None:
    if Depth >= KMaxDepth or Shape.KindValue not in KLeafKinds | KTypeArguments.keys():
        raise ValueError("Unsupported or excessively deep Fusion entity wire type")
    if len(Shape.Arguments) != KTypeArguments.get(Shape.KindValue, 0):
        raise ValueError("Fusion entity wire type has an invalid argument count")
    if Shape.KindValue == "object" and (
        not Shape.ClassGuid
        or Shape.ClassGuid.upper() not in Catalog.Classes
        or not Catalog.Classes[Shape.ClassGuid.upper()].IsValue
    ):
        raise ValueError("Fusion entity object requires a declared value class")
    if Shape.ClassGuid and Shape.KindValue not in ("object", "ref"):
        raise ValueError(
            "Fusion entity class constraint requires an object or reference"
        )
    if (
        type(Shape.FixedCount) is not int
        or not 0 <= Shape.FixedCount <= KMaxCount
        or (Shape.FixedCount and Shape.KindValue != "fixed")
    ):
        raise ValueError("Invalid Fusion entity fixed sequence length")
    CheckFlag(Shape.HasMatrixRows)
    if Shape.HasMatrixRows and Shape.KindValue != "matrix":
        raise ValueError("Invalid Fusion entity matrix branch declaration")
    if Shape.AllowedInts and (
        Shape.KindValue not in ("u8", "u16", "u32", "u64", "i32")
        or len(Shape.AllowedInts) > KMaxCount
        or any(type(Value) is not int for Value in Shape.AllowedInts)
    ):
        raise ValueError("Invalid Fusion entity constrained integer vocabulary")
    if Shape.Members and Shape.KindValue != "struct":
        raise ValueError("Fusion entity ordered fields require a struct type")
    Names = tuple(Field.FieldName for Field in Shape.Members)
    if len(Names) > KMaxCount or len(set(Names)) != len(Names) or not all(Names):
        raise ValueError("Invalid Fusion entity ordered field declarations")
    for Field in Shape.Members:
        CheckFlag(Field.IsSaved)
        if not Field.IsSaved:
            raise ValueError("Fusion entity callback fields must all be persisted")
        CheckWireType(Field.ValueType, Catalog, Depth + 1)
    for Argument in Shape.Arguments:
        CheckWireType(Argument, Catalog, Depth + 1)
