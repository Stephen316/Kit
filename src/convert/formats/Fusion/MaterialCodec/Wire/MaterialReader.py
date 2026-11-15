from math import isfinite as IsFinite
from struct import unpack as UnpackValue

from convert.formats.Fusion.MaterialCodec.Limits import KMaxCount, KMaxString
from convert.formats.Fusion.MaterialCodec.Wire.MaterialCursor import MaterialCursor


# the material reader contract needs a dedicated boundary so typed appearance properties retain their native identifiers
class MaterialReader(MaterialCursor):

    # the u int operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
    def ReadUInt(self) -> int:
        return int(UnpackValue("<I", self.TakeBytes(4))[0])

    # the small operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
    def ReadSmall(self) -> int:
        return self.TakeBytes(1)[0]

    # the int operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
    def ReadInt(self) -> int:
        return int(UnpackValue("<i", self.TakeBytes(4))[0])

    # the count operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
    def ReadCount(self, Upper: int = KMaxCount) -> int:
        Count = self.ReadUInt()
        if Count > Upper:
            raise ValueError("Fusion material count exceeds the size limit")
        return Count

    # the float operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
    def ReadFloat(self) -> float:
        Value = float(UnpackValue("<d", self.TakeBytes(8))[0])
        if not IsFinite(Value):
            raise ValueError("Fusion material scalar must be finite")
        return Value

    # the bool operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
    def ReadBool(self) -> bool:
        Value = self.TakeBytes(1)[0]
        if Value not in (0, 1):
            raise ValueError("Invalid Fusion material boolean")
        return bool(Value)

    # the text operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
    def ReadText(self) -> str:
        return self.TakeBytes(self.ReadCount(KMaxString)).decode("utf-8")
