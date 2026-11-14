from convert.formats.Fusion.DocumentCodec.Materials.StoredValue import (
    KInputValue,
    StoredValue,
)
from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.FamilyFields import (
    KDirections,
)
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


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
