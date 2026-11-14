from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


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
