from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


def MakeTagPrefix() -> tuple[KGeometryValue, ...]:
    return (3, 3, -1, CountedText("generic_tag_attrib_def "), 1)
