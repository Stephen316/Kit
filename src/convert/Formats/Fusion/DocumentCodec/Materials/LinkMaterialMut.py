from convert.Formats.Fusion.DocumentCodec.Materials.BuildMaterial import BuildMaterial
from convert.Formats.Fusion.DocumentCodec.Materials.PhysicalValue import PhysicalValue
from convert.Formats.Fusion.DocumentCodec.Materials.VisualValue import VisualValue
from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState


# link material must resolve unambiguously so appearance references remain connected to their owning entities
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
