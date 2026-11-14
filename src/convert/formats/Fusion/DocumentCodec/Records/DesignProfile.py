from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.EntityCodec.Vocabulary.ReadCatalog import ReadCatalog

KNamedKinds = ("form", "part")


def DesignProfile(Author: AuthorState) -> EntityProfile:
    Bindings = (
        ("ComponentBase", "rACTComponent", 100),
        ("ComponentBaseInstances", "rACTInstances", 101),
        ("ComponentBaseInstance", "rACTInstance", 102),
    )
    Targets: list[ExternalTarget] = []
    for NameValue, FieldName, ObjectId in Bindings:
        Shape = next(
            Member.ValueType
            for Member in Author.ByName[NameValue].Value.Members
            if Member.FieldName == FieldName
        )
        Targets.append(
            ExternalTarget(Author.Policy.ActSegmentId, ObjectId, Shape.ClassGuid)
        )
    return EntityProfile(
        "98542EB9-A4F2-4137-A808-DBB5B3CD6159",
        tuple(Schema.Value for Schema in Author.Schemas),
        tuple(Targets),
        ReadCatalog().NamedTypes if Author.SpecValue.ProfileKind in KNamedKinds else (),
    )
