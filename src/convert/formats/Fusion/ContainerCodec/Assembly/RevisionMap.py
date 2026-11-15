from uuid import UUID as ParseUuid

from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue

# the change types order must stay explicit so archive members retain their native ownership and reference relationships
KChangeTypes = (
    "Appearance",
    "Geometry",
    "PhysicalMaterial",
    "Properties",
    "StructureChange",
    "Transform",
)


# revision map needs an explicit validity boundary so archive members retain their native ownership and reference relationships
def RevisionMap(Value: str) -> ValueMap[KEntityValue]:
    Identifier = ParseUuid(Value)
    if not Identifier.int or str(Identifier) != Value:
        raise ValueError("Invalid Fusion assembly revision identifier")
    return ValueMap(tuple(ValuePair(NameValue, Value) for NameValue in KChangeTypes))
