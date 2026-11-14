from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec

KDeprecated = frozenset(("texture_MapChannel", "unifiedbitmap_MapChannel"))


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
