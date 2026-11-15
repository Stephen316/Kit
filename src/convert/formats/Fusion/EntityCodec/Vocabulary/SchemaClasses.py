from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeRoot import KNativeRoot
from convert.formats.Fusion.EntityCodec.Vocabulary.ValueClasses import ValueClasses


# the schema classes contract needs a shared interpretation so entity identifiers retain their schema and reference meaning
def SchemaClasses(Schema: ClassSchema) -> tuple[str, ...]:
    Bases = (
        (Schema.BaseGuid,)
        if Schema.BaseGuid and Schema.BaseGuid.upper() != KNativeRoot
        else ()
    )
    Values = tuple(
        Identity
        for Field in Schema.Members
        for Identity in ValueClasses(Field.ValueType)
    )
    return Bases + Values
