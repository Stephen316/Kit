from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType

KVectorName = "Vector"

KTypeError = "Unsupported Fusion entity named metadata metatype"

KElementError = "Unsupported Fusion named vector element metatype"


def NamedShape(TypeName: str, ElementName: str, Catalog: EntityCatalog) -> WireType:
    if TypeName != KVectorName:
        if ElementName:
            raise ValueError(KTypeError)
        return NamedKind(TypeName, Catalog, KTypeError)
    if ElementName == KVectorName:
        raise ValueError(KElementError)
    return WireType("sequence", (NamedKind(ElementName, Catalog, KElementError),))


def NamedKind(TypeName: str, Catalog: EntityCatalog, Message: str) -> WireType:
    Shape = Catalog.NamedTypes.get(TypeName)
    if Shape is not None:
        return Shape
    Schema = Catalog.Classes.get(TypeName.upper())
    if Schema is None or not Schema.IsValue or Schema.IsOpaque:
        raise ValueError(Message)
    return WireType("object", ClassGuid=Schema.ClassGuid)
