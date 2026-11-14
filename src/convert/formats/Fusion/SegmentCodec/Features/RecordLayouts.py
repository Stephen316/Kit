from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.ManagedLayout import (
    KManagedLayout,
)


def RecordLayouts(
    Layouts: tuple[ClassLayout, ...],
) -> tuple[bool, tuple[ClassLayout, ...]]:
    if Layouts[0] == KManagedLayout:
        return False, Layouts[:1]
    Boundary = Layouts.index(KManagedLayout)
    return True, Layouts[:Boundary]
