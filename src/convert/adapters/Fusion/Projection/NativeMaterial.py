from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.Formats.Fusion.DocumentCodec.Materials.ProjectMaterial import (
    ProjectMaterial,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.ReadMatRefs import (
    ReadMatRefs,
)


# native material needs an explicit validity boundary so public document claims remain grounded in native records
def NativeMaterial(ModelValue: DocumentModel) -> MaterialSpec:
    Bodies = ReadMatRefs(ModelValue, "physicalMaterial")
    if any(Package is None for Package, _ in Bodies):
        raise ValueError("Fusion body has an undefined physical material")
    Found = Bodies or ReadMatRefs(ModelValue, "defaultPhysicalMaterial")
    Assets = tuple(
        (Package, Identity) for Package, Identity in Found if Package is not None
    )
    if len(Assets) > 1:
        raise ValueError("Fusion document uses more than one physical material")
    return ProjectMaterial(*Assets[0]) if Assets else MaterialSpec()
