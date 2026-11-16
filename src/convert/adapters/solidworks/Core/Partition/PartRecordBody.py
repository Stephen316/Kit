from collections.abc import Iterator


# limited record bodies retain the native kind and optional marker boundary
def FindPartBodies(
    DataValue: bytes, KindValue: int, Width: int, *, HasMarker: bool = False
) -> Iterator[int]:
    Token = bytes((0, KindValue))
    Offset = 0
    while (Record := DataValue.find(Token, Offset)) >= 0:
        Offset = Record + 1
        Start = Record + len(Token)
        if HasMarker and DataValue[Start : Start + 1] == b"\xff":
            Start += 1
        if Start + Width <= len(DataValue):
            yield Start
