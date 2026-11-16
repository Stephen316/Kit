from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# invalid boundary representation references input must fail here so topology identity survives native history reconstruction
def CheckBrepRefs(Records: tuple[GeometryRecord, ...], RootCount: int) -> None:
    if not 2 <= RootCount <= len(Records) or Records[0].NameValue != "asmheader":
        raise ValueError("Fusion BRep root table is invalid")
    if any(Record.NameValue != "body" for Record in Records[1:RootCount]):
        raise ValueError("Fusion BRep top-level root is not a body")
    for Record in Records:
        for Value in Record.Fields:
            if isinstance(Value, EntityRef) and not -1 <= Value.Index < len(Records):
                raise ValueError("Fusion BRep reference leaves its active table")
