from types import MappingProxyType as ReadOnlyMap

from convert.formats.Fusion.SegmentCodec.Features.Schema.SketchLayout import (
    KSketchLayout,
)
from convert.formats.Fusion.SegmentCodec.Features.Schema.ExtrudeLayout import (
    KExtrudeLayout,
)
from convert.formats.Fusion.SegmentCodec.Features.Schema.ProfileLayout import (
    KProfileLayout,
)
from convert.formats.Fusion.SegmentCodec.Features.Schema.BodyLayout import KBodyLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.CoreLayout import KCoreLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.ComputeLayout import (
    KComputeLayout,
)
from convert.formats.Fusion.SegmentCodec.Features.Schema.NodeLayout import KNodeLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.ToolLinkLayout import (
    KToolLinkLayout,
)
from convert.formats.Fusion.SegmentCodec.Features.Schema.MultiLayout import KMultiLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.ActionLayout import (
    KActionLayout,
)
from convert.formats.Fusion.SegmentCodec.Features.Schema.ManagedLayout import (
    KManagedLayout,
)
from convert.formats.Fusion.SegmentCodec.Features.Schema.ToolLayout import KToolLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.EntityLayout import (
    KEntityLayout,
)

KFeatureLayouts = ReadOnlyMap(
    {
        Layout.Stamp.ClassGuid.upper(): Layout
        for Layout in (
            KSketchLayout,
            KExtrudeLayout,
            KProfileLayout,
            KBodyLayout,
            KCoreLayout,
            KComputeLayout,
            KNodeLayout,
            KToolLinkLayout,
            KMultiLayout,
            KActionLayout,
            KManagedLayout,
            KToolLayout,
            KEntityLayout,
        )
    }
)
