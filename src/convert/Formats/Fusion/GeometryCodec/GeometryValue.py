from typing import TypeAlias

from convert.Formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken

# the geometry value variants need one shared contract so geometry serialization cannot omit a supported value shape
KGeometryValue: TypeAlias = (  # lgtm[py/unused-global-variable]
    int | float | tuple[float, float, float] | EntityRef | CountedText | KeywordToken
)
