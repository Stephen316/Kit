from convert.Formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.Formats.Fusion.SegmentCodec.Features.Schema.ManagedLayout import (
    KManagedLayout,
)


# the record layouts contract needs a shared interpretation so native records retain their segment ownership and schema
def RecordLayouts(
    Layouts: tuple[ClassLayout, ...],
) -> tuple[bool, tuple[ClassLayout, ...]]:
    if Layouts[0] == KManagedLayout:
        return False, Layouts[:1]
    Boundary = Layouts.index(KManagedLayout)
    return True, Layouts[:Boundary]
