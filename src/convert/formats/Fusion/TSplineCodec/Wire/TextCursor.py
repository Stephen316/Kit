from dataclasses import dataclass


# text cursor needs an explicit state contract so control cage topology retains its native connectivity
@dataclass
class TextCursor:
    Records: tuple[tuple[str, ...], ...]
    Position: int = 0

    # the kind decision must stay consistent so control cage topology retains its native connectivity
    def HasKind(self, KindValue: str) -> bool:
        return (
            self.Position < len(self.Records)
            and self.Records[self.Position][0] == KindValue
        )

    # the fields operation needs a distinct decoding boundary so control cage topology retains its native connectivity
    def ReadFields(self, KindValue: str, FieldCount: int = -1) -> tuple[str, ...]:
        if not self.HasKind(KindValue):
            raise ValueError("TSM record order or kind is unsupported: " + KindValue)
        Fields = self.Records[self.Position][1:]
        self.Position += 1
        if FieldCount >= 0 and len(Fields) != FieldCount:
            raise ValueError("TSM record field count differs: " + KindValue)
        return Fields
