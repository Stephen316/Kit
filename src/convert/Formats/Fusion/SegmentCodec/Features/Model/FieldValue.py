from typing import TypeAlias

from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.Formats.Fusion.SegmentCodec.Features.Model.VectorValue import VectorValue

# the field value variants need one shared contract so segment reconstruction cannot omit a supported value shape
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
