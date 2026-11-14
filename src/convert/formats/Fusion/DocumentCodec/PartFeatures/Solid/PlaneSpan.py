from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan

KPlaneSpan: TypeAlias = LineSpan | ArcSpan
KPlaneLoop: TypeAlias = tuple[KPlaneSpan, ...]
