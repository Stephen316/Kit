from convert.Formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


# the attribute operation needs a consistent construction rule so native topology can resolve its owning modeling operation
def MakeAttribute(
    Owner: int,
    Family: str,
    Payload: tuple[KGeometryValue, ...],
    NextLink: int = -1,
    PriorLink: int = -1,
) -> GeometryRecord:
    return GeometryRecord(
        "ATTRIB_CUSTOM-attrib",
        (
            EntityRef(-1),
            -1,
            EntityRef(NextLink),
            EntityRef(PriorLink),
            EntityRef(Owner),
            CountedText(Family),
            *Payload,
        ),
    )
