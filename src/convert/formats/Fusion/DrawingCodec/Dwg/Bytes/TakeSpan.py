def TakeSpan(DataValue: bytes, Offset: int, SpanSize: int, Label: str) -> bytes:
    if Offset < 0 or SpanSize < 0 or Offset + SpanSize > len(DataValue):
        raise ValueError(f"DWG {Label} lies outside the available data")
    return DataValue[Offset : Offset + SpanSize]
