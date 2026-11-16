from convert.Formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.CheckAssetRefs import (
    CheckAssetRefs,
)
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


# bind manager needs an explicit validity boundary so model state retains its native feature and ownership relationships
def BindManager(
    Fields: dict[str, KEntityValue], Parts: dict[str, MaterialPart]
) -> tuple[str, MaterialPackage | None]:
    PartName = Fields.get("partName")
    if not isinstance(PartName, str):
        raise ValueError("Material manager requires a part name")
    if not PartName:
        for FieldName in (
            "PhysicalMaterialAssetReferences",
            "VisualMaterialAssetReferences",
        ):
            References = Fields.get(FieldName)
            if not isinstance(References, ValueSeries) or References.Items:
                raise ValueError("Material manager references assets without a package")
        return "", None
    FullName = "ProteinAssets.BlobParts/" + PartName
    if FullName not in Parts:
        raise ValueError("Document material manager package is missing")
    Package = Parts[FullName].Package
    CheckAssetRefs(Fields, Package, "PhysicalMaterial", "physicalmaterial")
    CheckAssetRefs(Fields, Package, "VisualMaterial", "materialappearance")
    return FullName, Package
