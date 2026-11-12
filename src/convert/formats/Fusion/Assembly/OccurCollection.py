from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor

# collection identity ties stored sibling order back to its owning component
KOccurCollection = "904F885E-D859-4755-A7EF-6EBED8732FAD"


# validate the collection before trusting its order and repeated ownership links
def ReadOccurColl(DataValue: bytes) -> tuple[int, tuple[int, ...]]:
    Cursor = MetaCursor(DataValue)
    Prefix = Cursor.TakeBytes(2)
    if Prefix == b"\0\1":
        if Cursor.ReadWord() != 0:
            raise ValueError("Unsupported Fusion occurrence collection attributes")
    elif Prefix != bytes(2):
        raise ValueError("Unsupported Fusion occurrence collection prefix")
    if Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Invalid Fusion occurrence collection marker")
    _ = Cursor.ReadLong()
    if Cursor.TakeBytes(7) != b"\0\1\1\0\0\0\0":
        raise ValueError("Invalid Fusion occurrence collection header")
    Count = Cursor.ReadCount(100000)
    if len(DataValue) - Cursor.Offset != 11 * (Count + 1):
        raise ValueError("Invalid Fusion occurrence collection extent")
    Members = tuple(ReadNativeRef(Cursor) for _ in range(Count))
    if len(set(Members)) != Count:
        raise ValueError("Duplicate Fusion occurrence collection member")
    return ReadNativeRef(Cursor), Members
