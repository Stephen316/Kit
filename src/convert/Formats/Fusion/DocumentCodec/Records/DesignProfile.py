from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.Formats.Fusion.EntityCodec.Vocabulary.ReadCatalog import ReadCatalog

# the named kinds order must stay explicit so model state retains its native feature and ownership relationships
KNamedKinds = ("form", "part")


# the design profile contract needs a shared interpretation so model state retains its native feature and ownership relationships
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
