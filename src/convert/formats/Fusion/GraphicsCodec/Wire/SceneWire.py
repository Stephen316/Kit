from convert.formats.Fusion.GraphicsCodec.Wire.NumericWire import NumericWire


class SceneWire(NumericWire):
    def CountValue(self, Value: int | None, Format: str = "<I") -> int:
        Result = self.Integer(Value, Format)
        if not 0 <= Result <= 1000000:
            raise ValueError("Graphics collection count exceeds qualified limit")
        return Result

    def TextValue(self, Value: str | None) -> str:
        if not self.IsReading and type(Value) is not str:
            raise ValueError("Expected a graphics string")
        Encoded = None if Value is None else Value.encode("utf-16le")
        Length = self.CountValue(None if Encoded is None else len(Encoded) // 2)
        return self.Transfer(Length * 2, Encoded).decode("utf-16le")

    def OptionalText(self, Value: str | None) -> str | None:
        return self.TextValue(Value) if self.IsFlag(Value is not None) else None

    def OptionalMat(self, Value: tuple[float, ...] | None) -> tuple[float, ...] | None:
        return self.Vector(Value, 16) if self.IsFlag(Value is not None) else None

    def ExpectText(self, Value: str) -> None:
        if self.TextValue(Value) != Value:
            raise ValueError("Unexpected Fusion graphics class or marker")

    def EmptyLinks(self, Count: int) -> None:
        if any(tuple(self.IsFlag(False) for _ in range(Count))):
            raise ValueError("Unsupported linked graphics callback")
