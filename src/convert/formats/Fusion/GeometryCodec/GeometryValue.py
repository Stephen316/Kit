from typing import TypeAlias

from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken

KGeometryValue: TypeAlias = (  # lgtm[py/unused-global-variable]
    int | float | tuple[float, float, float] | EntityRef | CountedText | KeywordToken
)
