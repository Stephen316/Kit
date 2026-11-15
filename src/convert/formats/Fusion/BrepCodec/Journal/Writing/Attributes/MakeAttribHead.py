from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# the attribute head operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeAttribHead(
    Links: AttribLinks, Family: str, Attribute: int = -1
) -> tuple[KAsmToken, ...]:
    return (
        (12, Attribute),
        (4, -1),
        (12, Links.NextAttrib),
        (12, Links.PriorAttrib),
        (12, Links.OwnerRef),
        (7, Family),
    )
