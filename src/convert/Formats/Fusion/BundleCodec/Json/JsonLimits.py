from convert.Formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue


# invalid json tree input must fail here so linked archive members retain their document relationships
def CheckJsonTree(Value: KJsonValue) -> None:
    Pending = [(Value, 0)]
    Count = 0
    TextBytes = 0
    while Pending:
        Current, Depth = Pending.pop()
        Count += 1
        if Count > 100_000 or Depth > 32:
            raise ValueError("Fusion bundle JSON exceeds structural limits")
        if isinstance(Current, dict):
            Pending.extend((Child, Depth + 1) for Child in Current)
            Pending.extend((Child, Depth + 1) for Child in Current.values())
        elif isinstance(Current, list):
            Pending.extend((Child, Depth + 1) for Child in Current)
        elif isinstance(Current, str):
            Length = len(Current.encode("utf-8"))
            TextBytes += Length
            if Length > 1024 * 1024 or TextBytes > 4 * 1024 * 1024:
                raise ValueError("Fusion bundle JSON string exceeds byte limit")
