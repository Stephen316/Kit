from convert.adapters.Fusion.State.Types.BrepTypes import KBrepTypes
from convert.adapters.Fusion.State.Types.ContainerTypes import KContainerTypes
from convert.adapters.Fusion.State.Types.DocumentTypes import KDocumentTypes
from convert.adapters.Fusion.State.Types.EntityTypes import KEntityTypes
from convert.adapters.Fusion.State.Types.GeometryTypes import KGeometryTypes
from convert.adapters.Fusion.State.Types.GraphicsTypes import KGraphicsTypes
from convert.adapters.Fusion.State.Types.MaterialTypes import KMaterialTypes
from convert.adapters.Fusion.State.Types.MetaIndexTypes import KMetaIndexTypes
from convert.adapters.Fusion.State.Types.SegmentTypes import KSegmentTypes

KStateTypes: tuple[type[object], ...] = (
    *KBrepTypes,
    *KContainerTypes,
    *KDocumentTypes,
    *KEntityTypes,
    *KGeometryTypes,
    *KGraphicsTypes,
    *KMaterialTypes,
    *KMetaIndexTypes,
    *KSegmentTypes,
)

KStateNames = {
    f"{ClassType.__module__}.{ClassType.__name__}": ClassType
    for ClassType in KStateTypes
}
