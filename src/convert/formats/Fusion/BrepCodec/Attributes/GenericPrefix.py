from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


# the tag prefix operation needs a consistent construction rule so native topology can resolve its owning modeling operation
def MakeTagPrefix() -> tuple[KGeometryValue, ...]:
    return (3, 3, -1, CountedText("generic_tag_attrib_def "), 1)
