from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage


# the mat part operation needs a consistent construction rule so appearance references remain connected to their owning entities
def BuildMatPart(Design: DesignResult) -> tuple[ContainerPart, ...]:
    if Design.Materials is None:
        return ()
    Material = Design.Materials
    return (
        ContainerPart(
            "ProteinAssets.BlobParts/" + Material.Identity.PartName,
            EmitPackage(Material.Package),
        ),
    )
