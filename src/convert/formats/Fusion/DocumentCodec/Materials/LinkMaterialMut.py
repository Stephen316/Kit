from convert.formats.Fusion.DocumentCodec.Materials.BuildMaterial import BuildMaterial
from convert.formats.Fusion.DocumentCodec.Materials.PhysicalValue import PhysicalValue
from convert.formats.Fusion.DocumentCodec.Materials.VisualValue import VisualValue
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


def LinkMaterialMut(Author: AuthorState) -> None:
    Author.Materials = BuildMaterial(Author.SpecValue.Material)
    Identity = Author.Materials.Identity
    Author.Change(
        "protein",
        PhysicalMaterialAssetReferences=[Identity.PhysicalId],
        PhysicalMaterialRefCountVector=[1],
        VisualMaterialAssetReferences=[Identity.AppearanceId],
        VisualMaterialRefCountVector=[1],
        partName=Identity.PartName,
    )
    Author.Change(
        "body",
        physicalMaterial=PhysicalValue(Author),
        visualMaterial=VisualValue(Author),
    )
