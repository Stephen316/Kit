from struct import pack as PackValue


# shared break tag length setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def BreakTagLength(Payload: bytes, PrimaryId: str) -> bytes:
    TextBytes = PrimaryId.encode("ascii")
    StringField = bytes((7, len(TextBytes))) + TextBytes
    Original = b"\x04" + PackValue("<q", len(TextBytes)) + StringField
    Modified = b"\x04" + PackValue("<q", len(TextBytes) + 1) + StringField
    assert Payload.count(Original) == 1
    return Payload.replace(Original, Modified, 1)
