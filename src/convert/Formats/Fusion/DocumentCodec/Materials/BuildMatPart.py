from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.Formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage


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
