from typing import TypeAlias

from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.SegmentCodec.Features.Model.VectorValue import VectorValue

KFieldValue: TypeAlias = (  # lgtm[py/unused-global-variable]
    bool
    | int
    | float
    | str
    | LocalRef
    | VectorValue
    | tuple[LocalRef | None, ...]
    | None
)
