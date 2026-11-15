from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan

# the plane span variants need one shared contract so solid feature construction cannot omit a supported value shape
KPlaneSpan: TypeAlias = LineSpan | ArcSpan

# the plane loop shape must stay shared so solid feature construction uses one contract for compatible values
KPlaneLoop: TypeAlias = tuple[KPlaneSpan, ...]
