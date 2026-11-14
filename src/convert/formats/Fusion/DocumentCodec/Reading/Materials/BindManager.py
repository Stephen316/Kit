from convert.formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.formats.Fusion.DocumentCodec.Reading.Materials.CheckAssetRefs import (
    CheckAssetRefs,
)
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


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
