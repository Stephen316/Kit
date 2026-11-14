from collections.abc import Mapping

from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeCatalog import NativeCatalog
from convert.formats.Fusion.EntityCodec.Vocabulary.PickSchema import PickSchema
from convert.formats.Fusion.EntityCodec.Vocabulary.SchemaClasses import SchemaClasses
from convert.formats.Fusion.EntityCodec.Vocabulary.ValueClasses import ValueClasses


def CloseCatalog(
    Chosen: Mapping[str, ClassSchema],
    Catalog: NativeCatalog,
    Targets: tuple[ExternalTarget, ...],
) -> tuple[ClassSchema, ...]:
    Selected = dict(Chosen)
    Pending = [
        Identity for Schema in Selected.values() for Identity in SchemaClasses(Schema)
    ]
    Pending.extend(
        Target.ClassGuid
        for Target in Targets
        if Target.ClassGuid.upper() in Catalog.Classes
    )
    Pending.extend(
        Identity
        for Named in Catalog.NamedTypes
        for Identity in ValueClasses(Named.ValueType)
    )
    while Pending:
        Identity = Pending.pop().upper()
        if Identity in Selected:
            continue
        if len(Selected) >= KMaxCount:
            raise ValueError("Fusion native schema closure exceeds the class limit")
        Schema = PickSchema(Identity, None, Catalog)
        Selected[Identity] = Schema
        Pending.extend(SchemaClasses(Schema))
    return tuple(Selected[Identity] for Identity in sorted(Selected))
