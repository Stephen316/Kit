from dataclasses import dataclass


@dataclass
class TextCursor:
    Records: tuple[tuple[str, ...], ...]
    Position: int = 0

    def HasKind(self, KindValue: str) -> bool:
        return (
            self.Position < len(self.Records)
            and self.Records[self.Position][0] == KindValue
        )

    def ReadFields(self, KindValue: str, FieldCount: int = -1) -> tuple[str, ...]:
        if not self.HasKind(KindValue):
            raise ValueError("TSM record order or kind is unsupported: " + KindValue)
        Fields = self.Records[self.Position][1:]
        self.Position += 1
        if FieldCount >= 0 and len(Fields) != FieldCount:
            raise ValueError("TSM record field count differs: " + KindValue)
        return Fields
