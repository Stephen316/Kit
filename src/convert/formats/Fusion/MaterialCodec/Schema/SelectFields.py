from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec

# the deprecated vocabulary must stay centralized so material reconstruction agrees on supported native identities
KDeprecated = frozenset(("texture_MapChannel", "unifiedbitmap_MapChannel"))


# select fields must resolve unambiguously so typed appearance properties retain their native identifiers
def SelectFields(
    Fields: tuple[PropertySpec, ...], IsDefinition: bool
) -> tuple[PropertySpec, ...]:
    return tuple(
        Field
        for Field in Fields
        if Field.IsDefinition == IsDefinition
        and (
            IsDefinition
            or (not Field.IsReadOnly and Field.FieldName not in KDeprecated)
        )
    )
