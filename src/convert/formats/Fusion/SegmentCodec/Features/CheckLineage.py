from typing import cast as CastValue

from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxLineage
from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.ExtrudeLayout import (
    KExtrudeLayout,
)
from convert.formats.Fusion.SegmentCodec.Features.Schema.LayoutCatalog import (
    KFeatureLayouts,
)
from convert.formats.Fusion.SegmentCodec.Features.Schema.ManagedLayout import (
    KManagedLayout,
)
from convert.formats.Fusion.SegmentCodec.Features.Schema.SketchLayout import (
    KSketchLayout,
)


def CheckLineage(Lineage: tuple[ClassStamp, ...]) -> tuple[ClassLayout, ...]:
    if type(Lineage) is not tuple or not 1 <= len(Lineage) <= KMaxLineage:
        raise ValueError("Invalid Fusion feature class lineage")
    Layouts: list[ClassLayout] = []
    Expected: str | None = None
    Supported = (KSketchLayout, KExtrudeLayout, KManagedLayout)
    for Stamp in Lineage:
        if (
            not isinstance(CastValue(object, Stamp), ClassStamp)
            or type(Stamp.ClassGuid) is not str
            or type(Stamp.BaseGuid) is not str
            or type(Stamp.SchemaVersion) is not int
        ):
            raise ValueError("Invalid Fusion feature class declaration")
        Identity = Stamp.ClassGuid.upper()
        Layout = KFeatureLayouts.get(Identity)
        if (
            Layout is None
            or (Expected is not None and Identity != Expected)
            or (not Layouts and Layout not in Supported)
            or Stamp.SchemaVersion != Layout.Stamp.SchemaVersion
            or Stamp.BaseGuid.upper() != Layout.Stamp.BaseGuid.upper()
        ):
            raise ValueError("Unsupported Fusion feature class or inheritance version")
        Layouts.append(Layout)
        Expected = Layout.Stamp.BaseGuid.upper()
    if Expected != "":
        raise ValueError("Incomplete Fusion feature class lineage")
    return tuple(Layouts)
