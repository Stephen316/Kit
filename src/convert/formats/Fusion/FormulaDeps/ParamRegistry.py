from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor

# the registry reciprocates the collection and assigns exact names to native identities
KParamRegistry = "E276745D-D84E-40D5-88BC-8C94DD4ACCDF"


# registry dependency slots describe table membership rather than expression edges
def ReadTableRefs(
    Cursor: MetaCursor,
    CollectionId: int,
    Members: frozenset[int],
    MemberOrder: tuple[int, ...] | None = None,
) -> None:
    if Cursor.TakeBytes(1) != b"\1" or Cursor.ReadWord() != len(Members) + 1:
        raise ValueError("Unknown Fusion parameter registry header")
    References: list[int] = []
    for _ in range(len(Members) + 1):
        References.append(ReadNativeRef(Cursor))
        if Cursor.TakeBytes(4) != bytes(4):
            raise ValueError("Unknown Fusion parameter registry reference")
    if (
        References[0] != CollectionId
        or frozenset(References[1:]) != Members
        or (MemberOrder is not None and tuple(References[1:]) != MemberOrder)
    ):
        raise ValueError("Fusion parameter registry references disagree")


# every visible name must resolve exactly once to a unique registered member
def ReadNameTable(
    BodyValue: bytes,
    CollectionId: int,
    Members: frozenset[int],
    *,
    MemberOrder: tuple[int, ...] | None = None,
) -> dict[int, str]:
    Cursor = MetaCursor(BodyValue)
    ReadTableRefs(Cursor, CollectionId, Members, MemberOrder)
    if Cursor.TakeBytes(1) != b"\0" or Cursor.ReadWord() != len(Members):
        raise ValueError("Invalid Fusion parameter registry name count")
    Names: dict[int, str] = {}
    for _ in range(len(Members)):
        NameValue = Cursor.ReadText(True, Maximum=1024)
        Identity = ReadNativeRef(Cursor)
        if not NameValue or Identity in Names:
            raise ValueError("Invalid Fusion parameter registry identity")
        Names[Identity] = NameValue
    if (
        Names.keys() != Members
        or len(set(Names.values())) != len(Members)
        or Cursor.Offset != len(BodyValue)
    ):
        raise ValueError("Fusion parameter registry names disagree")
    return Names
