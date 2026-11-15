from math import isfinite as IsFinite
from struct import pack as PackValue, unpack as UnpackValue, calcsize as CalcSize
from convert.formats.Fusion.GraphicsCodec.Wire.ByteStream import ByteStream


# the numeric wire contract needs a dedicated boundary so display geometry retains its entity and scene relationships
class NumericWire(ByteStream):

    # the flag decision must stay consistent so display geometry retains its entity and scene relationships
    def IsFlag(self, Value: bool | None) -> bool:
        if not self.IsReading and type(Value) is not bool:
            raise ValueError("Expected a boolean graphics field")
        Number = self.Integer(None if self.IsReading else int(bool(Value)), "<B")
        if Number not in (0, 1):
            raise ValueError("Noncanonical graphics boolean")
        return bool(Number)

    # scalar needs an explicit validity boundary so display geometry retains its entity and scene relationships
    def Scalar(self, Value: float | None, Format: str = "<f") -> float:
        if not self.IsReading and (type(Value) is not float or not IsFinite(Value)):
            raise ValueError("Expected a finite floating graphics field")
        Encoded = None if self.IsReading else PackValue(Format, Value)
        Result = float(UnpackValue(Format, self.Transfer(CalcSize(Format), Encoded))[0])
        if not IsFinite(Result):
            raise ValueError("Nonfinite graphics field")
        return Result

    # vector needs one geometric convention so display geometry retains its entity and scene relationships
    def Vector(
        self, Value: tuple[float, ...] | None, Count: int, Format: str = "<f"
    ) -> tuple[float, ...]:
        if not self.IsReading and (type(Value) is not tuple or len(Value) != Count):
            raise ValueError("Incorrect graphics vector length")
        return tuple(
            self.Scalar(None if Value is None else Value[Index], Format)
            for Index in range(Count)
        )
