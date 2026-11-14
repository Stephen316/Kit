from convert.adapters.base.AdapterInfo import AdapterInfo
from interchange.enums.EnumDocument import Capability

KReaderInfo = AdapterInfo(
    format_id="fusion.f3d",
    name="Autodesk Fusion",
    version="2.0",
    aliases=("f3d",),
    extensions=(".f3d",),
    part_extensions=(".f3d",),
    assembly_extensions=(".f3d",),
    capabilities=frozenset(
        {
            Capability.KParameters,
            Capability.KParamHistory,
            Capability.KEditableSketches,
            Capability.KConfigurations,
            Capability.KExpressions,
            Capability.KMaterials,
            Capability.KSupportPlanes,
            Capability.KSelections,
            Capability.KBodyStructure,
            Capability.KBrep,
            Capability.KAssemblies,
            Capability.KComponentDocs,
            Capability.KNativePayloads,
            Capability.KProvenance,
        }
    ),
)
