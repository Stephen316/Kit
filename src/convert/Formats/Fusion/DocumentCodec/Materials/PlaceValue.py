from convert.Formats.Fusion.DocumentCodec.Materials.StoredValue import (
    KInputValue,
    StoredValue,
)
from convert.Formats.Fusion.DocumentCodec.Materials.Vocabulary.FamilyFields import (
    KDirections,
)
from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.Formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


# the value operation needs a consistent construction rule so appearance references remain connected to their owning entities
def PlaceValue(
    Fields: dict[str, SchemaNode], Candidates: tuple[str, ...], Value: KInputValue
) -> tuple[PropertyValue, ...]:
    Present = tuple(Candidate for Candidate in Candidates if Candidate in Fields)
    if len(Present) != 1:
        raise ValueError("Material property has no place in its Fusion schema")
    Targets = (Present[0],) + tuple(
        Present[0] + "_" + Direction
        for Direction in KDirections
        if Present[0] + "_" + Direction in Fields
    )
    return tuple(
        PropertyValue(Target, StoredValue(Fields[Target], Value)) for Target in Targets
    )
