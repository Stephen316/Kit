from datetime import UTC, datetime as DateTime

from convert.Formats.Fusion.DocumentCodec.Materials.CheckMaterial import CheckMaterial
from convert.Formats.Fusion.DocumentCodec.Materials.CreateMatIds import CreateMatIds
from convert.Formats.Fusion.DocumentCodec.Materials.MaterialAssets import (
    IndexSchemas,
    MaterialAssets,
)
from convert.Formats.Fusion.DocumentCodec.Materials.Model.AuthoredMat import AuthoredMat
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.Formats.Fusion.DocumentCodec.Materials.Vocabulary.ReadMatSchema import (
    ReadMatSchema,
)
from convert.Formats.Fusion.MaterialCodec.Package.MakePackage import MakePackage
from convert.Formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


# the material operation needs a consistent construction rule so appearance references remain connected to their owning entities
def BuildMaterial(SpecValue: MaterialSpec) -> AuthoredMat:
    CheckMaterial(SpecValue)
    Identity = CreateMatIds()
    Schemas = ReadMatSchema()
    Assets = MaterialAssets(SpecValue, Identity, Schemas)
    Package = MakePackage(
        Identity.PackageId,
        Identity.AssetId,
        DateTime.now(UTC).isoformat(),
        SchemaClosure(tuple(Asset.SchemaName for Asset in Assets), Schemas),
        Assets,
    )
    return AuthoredMat(Identity, Package)


# schema closure needs an explicit validity boundary so appearance references remain connected to their owning entities
def SchemaClosure(
    Names: tuple[str, ...], Schemas: tuple[SchemaNode, ...]
) -> tuple[SchemaNode, ...]:
    Indexed = IndexSchemas(Schemas)
    Needed: set[str] = set()
    Pending = list(Names)
    while Pending:
        NameValue = Pending.pop()
        if NameValue in Needed:
            continue
        if NameValue not in Indexed:
            raise ValueError("Fusion material schema is absent from the vocabulary")
        Needed.add(NameValue)
        Pending.extend(
            dict(Child.Attributes)["val"]
            for Child in Indexed[NameValue].Children
            if Child.TagName == "Base"
        )
    return tuple(
        Declared for NameValue, Declared in Indexed.items() if NameValue in Needed
    )
